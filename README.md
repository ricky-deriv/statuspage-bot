# Statuspage Bot
A slack bot to interact with [Deriv's status page](https://deriv.statuspage.io/). 

# Prerequisites
- [Docker](https://www.docker.com/)

# Installation
1. Clone repository
2. Change to project directory
    ```
    cd statuspage-bot
    ```
3. Initialize secrets in `lib/.env`. For reference, [env.example](lib/env.example)
    - create a slack app if required [slack documentation](https://api.slack.com/apps)
4. Initialize  slack ids of allowed users to declare incident in `lib/.allowed_ids.json`. [allowed_ids.json.sample](lib/allowed_ids.json.sample)
5. Build container:
    ```
    make build
    ```


# Usage
1. Run the docker container:
    ```
    make run
    ```
