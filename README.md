# Super Hero Combat Simulator

This repo is dedicated to simulating Super Hero combat through WebSocket protocol and automation. The motivation is to provide a replicatable source for realtime combat simulation which provides a free data simulator for testing streaming applications. The objective of this repo is to only offer a WS API for spinning up a server for clients to interact with each through super hero fighting.

This repo doesn't provide guidance for creating multi-player frameworks, nor does it offer any user experience for Super Hero Combat. Gameplay is only intended to be *bot vs bot*, and pretty stupid bots at that, for the purpose of currating free (useless) data.

The work done herein couldn't be possible without the fantastic collection of Super Hero attribute data from [Super Hero API](https://www.superheroapi.com/)! Thanks!

![Super Hero Fight Marvel & DC](https://www.comicbasics.com/wp-content/uploads/2017/09/Best-Fighters-in-Marvel-Comics-1.jpg "Brawl!")

# Overview

## Server

The server instance will connect clients together to begin combat. It will wait for clients to login, and provide the number of contestants the client is willing to fight simultaneously. On login, the server will sort clients into their own lobby room by registering them to a game token. If no lobby room exists with the configured amount of participants the client is requesting then one is created. Once the number of participants is satisified, the server will call all clients to begin play, and iteratively let each client know when their turn is.

Upon completion of the game, the server will call all participants to indicate the game has finished. The clients are then signaled to close connection. At this time, all that is left is to clean up the DB registries which was monitoring game activities.

## Worker

This is where the clean up work is done. At the end of each gamge, the Server publishes a message to the `clean` channel in Redis where this work subscribes to. The worker consumes messages from this channel, and applies expiry times to all Redis Keys (found in the API section) while deleting all other objects.

This worker has incredibly simple tasks for the purpose of illustrating the native Pub/Sub capability in Redis. We aim to expand on this application's *worker* service in the Pub/Sub sub folder.

## Client

The client instance will connect to the server awaiting combat. The client provides a user identification, along with how many opponents it wants to play against in this current round. On login, if no user exists then the server will register the user. The user then waits for the server to slot all participants into the game and waits for acknowledgement that the game can start.

The user picks an action to send to the server, and then waits for the outcome of the combat against the selected opponent. After acknowledgement from the server in regard to the action, the user then waits for signal from the server for its next turn. If all opponents have been eliminated, then the server will broadcast back to all participants that the game has completed, and then the client will disconnect.

## Build DB

A simple script to pull Super Hero attributes from the [Super Hero API](https://www.superheroapi.com/), clean the data and store in the Redis DB in the `superheros` Hash. The script by default looks for the `superhero.json` file found in this repository to reduce the pulls required from the API. In the case where we want to get an updated version of the Super Hero collection, then we can run the following script to repull and store in `superher.json`.

```bash

export API_TOKEN=[Insert Super Hero API Token HERE]
export $(cat .env) && python3 build_db.py pull

```

An API Token can be generated at the home page of [Super Hero API](https://www.superheroapi.com/), by loggingin in with your Facebook account.


## Environmment Variables

| Variable Name  | Default   | Description                                                   |
|----------------|-----------|---------------------------------------------------------------|
| REDIS_HOST     | localhost | [str] Redis Host Address                                      |
| REDIS_PORT     | 6379      | [int] Redis Host Port                                         |
| REDIS_DB       | 0         | [int] Redis Databse                                           |
| REDIS_EXPIRY   | 30        | [int] Redis Key Expiry in seconds                             |
| WORKER_CHANNEL | CLEAN     | [str] Redis Pub/Sub Channel                                   |
| WEBSOCKET_HOST | localhost | [str] Websocket Server Address                                |
| WEBSOCKET_PORT | 5678      | [int] Websocket Server Port                                   |
| SERVER_SLEEP   | 5         | [float] Websocket Server sleep between Send/Receive messages  |
| LOBBY_TIMEOUT  | 5         | [float] Websocket Server timeout for idle games               |
| CLIENT_GAMES   | 10        | [int] Max number of games a BOT can play (-1 for no limit)    |
| API_TOKEN      | None      | [str] Super Hero API Key                                      |

# How to Use

## Local Development

To test/debug these services, each service can be started locally by executing the script in bash. A Redis service must be running, and can easily be started separate from the other docker services. The following commands will have the server application running locally

```bash

docker-compose up -d redis && \
export $(cat .env) && \
python3 build_db.py && \
python3 server.py && \
python3 worker.py

```

Once the server is up and running, we can deploy as many clients as we'd like with the following - repeat as necessary to meet required participants.

```bash

export $(cat .env) && python3 client.py

```

The Redis DB often requires a fresh slate for testing purposes. While we can't wipe anything specific in the Redis DB, we do have the option to flush the entire DB with the following command.

```bash

export REDIS_DB=0
redis-cli -h localhost -n ${REDIS_DB} -e FLUSHDB

```

## Production

Spinning up a production application with docker-compose is simple. Follow the commands below, replacing `${PLAYERS}` with the required participants.

```bash

export PLAYERS=10
docker-compose --env-file .env build && \
docker-compose --env-file .env up --scale player=${PLAYERS}

```

We can even load balance the server with the following

```bash

export PLAYERS=10
export LOADBALANCE=3
docker-compose --env-file .env build && \
docker-compose --env-file .env up --scale superhero_server=${LOADBALANCE} --scale player=${PLAYERS}

```

# Super Hero Attributes

This section described the alterations we make to the Super Hero API collection, and any in-game variability to bring the simulation richer features.

## Collection Attributes

Super Hero Health

$P_{Health}=max(10*(p_{Intelligence}*P_{Strength}*P_{Durability}),1)$

Super Hero Attack Damage

$P_{Damage}=max(10*(p_{Speed}*P_{Power}*P_{Combat}),1)$

Where $P$ denotes the Super Hero's Power Stats.

## In-Game calculations

To be introduced in later versions

# API

Data transmission uses a full duplex Websocket protocol to communicate between Server and Client. The project has benefitted with the ease of endpoint mapping similar to Flask's Route decorator from [Websockets Routes](https://pypi.org/project/websockets-routes/) help.

## Schema V1

### **/api/v1/login**

*Send* content requires following format

```json

{
    "PAYLOAD": {
        "USER": {{ %user% }}
    }
}
```

This payload sent to the server will match the contents of **USER** against existing users, and if no user exists then one will be created. The **USER TOKEN** is returned to the client. Here are the following registries to Redis

 * `user` Hash scanned for current user/ user entry created if use doesn't exist

*Received* content will be in the following format

```json
{
    "PAYLOAD": {
        "USER_TOKEN": {{ %user_token% }}
    }
}
```

### **/api/v1/game/find**

*Send* content requires the following format

```json

{
    "PAYLOAD": {
        "USER_TOKEN": {{ %user_token% }},
        "PARTICIPANTS": {{ %n_participants% }}
    }
}
```

This payload sent to the server will match the **USER TOKEN** to an open game in the lobby. If no game exists, then one will be created and configured with the number of **PARTICIPANTS** requested. Once a game has been created, a **GAME TOKEN** is provided while also selecting a super hero at random for the user. Here are the following registries to Redis

Creating/Finding Game
 * `games:players:%n_participants%` List scanned for possible open games matching **PARTICIPANTS**/ game entry created if none exist
 * `games:participants` Ordered Set incrementing the number of participants in **GAME TOKEN**
 * `games:%game_token%:participants` Key to register how many participants **GAME TOKEN** is configured for
 * `games:%game_token%:status` Key to monitor lobby room status for room registered to **GAME TOKEN**
 * `games:%game_token%:host` Key to register a psedue Host with **USER TOKEN** for room **GAME TOKEN**

Selecting Super Hero
 * `superhero` Hash database of superheros
 * `games:%game_token%:superheros` Set registering **USER TOKEN** and Super Hero ID to eliminate duplicate heros in match
 * `games:%game_token:superheros:%user_token%` Hash registering Super Hero's ID/ Attach/ Health per **USER TOKEN** in **GAME TOKEN**

*Received* content will be in the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }},
        "HERO_ID": {{ %id% }}
    },
    "STATUS": {
        "JOINED": "SUCCESFULL"
    }
}

```

### **/api/v1/game/lobby**

*Send* content requires the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }}, 
        "USER_TOKEN": {{ %user_token% }}
    }
}

```

This payload sent to the server will queue the user waiting for the game to start. Once the game's configured participants is reached, the game is declared to start, so no further users can enter. All users are brodast a message that the game will begin which is accompanied with the list of participant's heros.

The server then registers the users turn order, and then the server handles rotating each user's turn. On the broadcasted message indicating the game has started, each user waits for their turn to reach queue. A single user is allowed to provide an action, then the server rotates the order, and iteratively signals the next user to provide an action.

The lobby endpoint will also declare once a game has been completed by sending a broadcast message to all users that the game has reached it's end - allowing the users to finally exit connection with the server. Here are the following registries to Redis
 
 * `games:%game_token:order` List with **USER TOKEN** order for room **GAME TOKEN**
 * `games:%game_token%:status` Key to switch room registered to **GAME TOKEN** [Starting/In-Progress/Timed Out]
 * `games:participants` Ordered set to verify room participants is satisfied
 * `games:%game_token%:participants` Key configured how many participants for room **GAME TOKEN**
 * `games:%game_token%:superheros:%user_token%` Hash to monitor **USER TOKEN** super hero's attributes in **GAME TOKEN**

*Received* content for game start will be in the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }},
        "PARTICIPANTS": {{ %n_participants% }},
        "PARTICIPANTS_HEROS": {{ %heros% }},
    },
    "STATUS": {
        "GAME": "START"
    }
}

```

*Received* content for user's turn will be in the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }}
    },
    "STATUS": {
        "GAME": "USER'S TURN"
    }
}

```

*Received* content for completed game will be in the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }}
    },
    "STATUS": {
        "GAME": "COMPLETE"
    }
}

```

### **/api/v1/game/hero**

*Send* content requires the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }}, 
        "USER_TOKEN": {{ %user_token% }}
    }
}

```

Enpoint for retreiving user's heros in game. Any user can request another user's super hero attributes through this endpoint. Here are the following registries to Redis

 * `games:%game_token%:superheros:%user_token%` Hash to monitor **USER TOKEN** super hero's attributes in **GAME TOKEN**

*Received* content will be in the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }},
        "USER_TOKEN": {{ %user_token% }},
        "HERO": {{ %hero% }}
    },
    "STATUS": {
        "GAME": "HERO SPEC"
    }
}

```

### **/api/v1/game/action**

*Send* content requires the following format

```json

{
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }}, 
        "USER_TOKEN": {{ %user_token% }}, 
        "ENEMY_TOKEN": {{ %enemy_token% }},
        "ACTION": "ATTACK"
    }
}

```

The user sends an attack action to the server, with an opponent selected at random. The server then registers how much damage the opponent has taken in combat. The attacking user is then provided the details of the combat with the registered damage, and the enemy's before/after health. Here are the following registries to Redis

 * `game:%game_token%:logs` List archiving **GAME TOKEN** for analysis
 * `games:%game_token%:order` List of **GAME TOKEN** user order which the user will get ommitted from once dead
 * `games:%game_token%:superheros:%user_token%` Hash to monitor **USER TOKEN** super hero's attributes in **GAME TOKEN**

*Received* content will be in the following format

```json

{
    "TIMESTAMP": {{ %timestamp% }},
    "PAYLOAD": {
        "GAME_TOKEN": {{ %game_token% }},
        "USER_TOKEN": {{ %user_token% }}
    },
    "STATUS": {
        "ACTION": "ATTACK",
        "DETAILS": {
            "ENEMY_TOKEN": {{ %enemy_token% }},
            "ENEMY_DAMAGE": {{ %hero_attack$ }},
            "ENEMY_HEALTH_PRIOR": {{ %enemy_pre_health% }},
            "ENEMY_HEALTH_POST": {{ %enemy_post_health% }}
        }
    }
}

```

# TODO

 * Extend Client Actions to include more options
 * Build Unit Test Suit
 * Build Round Counter into turn_handler
 * Incorporate EXP for user completion/win
 * Incorporate User Ranking