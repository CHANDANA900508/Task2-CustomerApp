pipeline {

    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'UAT', 'PRODUCTION'],
            description: 'Select deployment environment'
        )

        choice(
            name: 'ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Select deployment action'
        )

        string(
            name: 'VERSION',
            defaultValue: '1.2',
            description: 'Docker image version'
        )

        choice(
            name: 'RUN_TESTS',
            choices: ['YES', 'NO'],
            description: 'Run application validation tests'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Required for production deployment'
        )
    }

    environment {
        IMAGE_NAME = 'customer-app'
        DB_CREDENTIALS_ID = 'customer-db-credentials'
        POWERSHELL = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
    }

    stages {

        stage('Resolve Configuration') {
            steps {
                script {

                    if (params.ENVIRONMENT == 'DEV') {

                        env.GIT_BRANCH_NAME = 'develop'
                        env.APP_NAME = 'customer-app-dev'
                        env.DB_CONTAINER = 'customer-db-dev'
                        env.NETWORK_NAME = 'customer-dev-net'
                        env.HOST_PORT = '8081'
                        env.APP_ENV = 'DEV'
                        env.DB_VOLUME = 'customer-db-dev-data'

                    } else if (params.ENVIRONMENT == 'UAT') {

                        env.GIT_BRANCH_NAME = 'release'
                        env.APP_NAME = 'customer-app-uat'
                        env.DB_CONTAINER = 'customer-db-uat'
                        env.NETWORK_NAME = 'customer-uat-net'
                        env.HOST_PORT = '8082'
                        env.APP_ENV = 'UAT'
                        env.DB_VOLUME = 'customer-db-uat-data'

                    } else if (params.ENVIRONMENT == 'PRODUCTION') {

                        if (params.CONFIRM_PROD != 'YES') {
                            error('Production deployment requires CONFIRM_PROD=YES')
                        }

                        env.GIT_BRANCH_NAME = 'main'
                        env.APP_NAME = 'customer-app-prod'
                        env.DB_CONTAINER = 'customer-db-prod'
                        env.NETWORK_NAME = 'customer-prod-net'
                        env.HOST_PORT = '8083'
                        env.APP_ENV = 'PRODUCTION'
                        env.DB_VOLUME = 'customer-db-prod-data'

                    } else {
                        error('Invalid environment selected')
                    }

                    echo '========================================'
                    echo 'RESOLVED DEPLOYMENT CONFIGURATION'
                    echo '========================================'
                    echo "Environment : ${env.APP_ENV}"
                    echo "Git Branch  : ${env.GIT_BRANCH_NAME}"
                    echo "Action      : ${params.ACTION}"
                    echo "Version     : ${params.VERSION}"
                    echo "Application : ${env.APP_NAME}"
                    echo "Database    : ${env.DB_CONTAINER}"
                    echo "Network     : ${env.NETWORK_NAME}"
                    echo "Host Port   : ${env.HOST_PORT}"
                    echo "DB Volume   : ${env.DB_VOLUME}"
                    echo "Run Tests   : ${params.RUN_TESTS}"
                    echo '========================================'
                }
            }
        }

        stage('Checkout Selected Branch') {
            steps {

                echo "Checking out branch: ${env.GIT_BRANCH_NAME}"

                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${env.GIT_BRANCH_NAME}"]],
                    userRemoteConfigs: [[
                        url: 'https://github.com/CHANDANA900508/Task2-CustomerApp.git'
                    ]]
                ])
            }
        }

        stage('Validate Version') {
            steps {

                script {

                    if (!(params.VERSION ==~ /^[0-9]+\.[0-9]+$/)) {
                        error("Invalid VERSION '${params.VERSION}'. Use format such as 1.2")
                    }

                    echo "Version ${params.VERSION} is valid."
                }
            }
        }

        stage('Build Docker Image') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "docker build -t customer-app:%VERSION% ."
                '''

                bat '''
                    docker images customer-app:%VERSION%
                '''
            }
        }

        stage('Ensure Docker Network') {
            steps {

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$network = docker network inspect $env:NETWORK_NAME 2>$null; if ($LASTEXITCODE -ne 0) { docker network create $env:NETWORK_NAME }"
                '''
            }
        }

        stage('Deploy Database') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                withCredentials([
                    usernamePassword(
                        credentialsId: 'customer-db-credentials',
                        usernameVariable: 'DB_USER',
                        passwordVariable: 'DB_PASSWORD'
                    )
                ]) {

                    bat '''
                        "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$existing = docker inspect $env:DB_CONTAINER 2>$null; if ($LASTEXITCODE -ne 0) { docker run -d --name $env:DB_CONTAINER --network $env:NETWORK_NAME -e MYSQL_ROOT_PASSWORD=$env:DB_PASSWORD -e MYSQL_DATABASE=customerdb -v $env:DB_VOLUME`:/var/lib/mysql mysql:8.0 }"
                    '''
                }
            }
        }

        stage('Wait for Database') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 10"
                '''
            }
        }

        stage('Deploy Application') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                withCredentials([
                    usernamePassword(
                        credentialsId: 'customer-db-credentials',
                        usernameVariable: 'DB_USER',
                        passwordVariable: 'DB_PASSWORD'
                    )
                ]) {

                    bat '''
                        "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "docker rm -f $env:APP_NAME 2>$null; docker run -d --name $env:APP_NAME --network $env:NETWORK_NAME -p $env:HOST_PORT`:8080 -e ENVIRONMENT=$env:APP_ENV -e VERSION=$env:VERSION -e DB_HOST=$env:DB_CONTAINER -e DB_USER=$env:DB_USER -e DB_PASSWORD=$env:DB_PASSWORD -e DB_NAME=customerdb customer-app:$env:VERSION"
                    '''
                }
            }
        }

        stage('Validate Deployment') {
            when {
                expression {
                    params.ACTION == 'DEPLOY'
                }
            }

            steps {

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Checking containers...'; docker ps --filter name=$env:APP_NAME; docker ps --filter name=$env:DB_CONTAINER"
                '''

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Checking Docker network...'; docker network inspect $env:NETWORK_NAME"
                '''

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 5; $health = Invoke-RestMethod http://localhost:$env:HOST_PORT/health; Write-Host 'Health check:'; $health | ConvertTo-Json; if ($health.status -ne 'UP') { throw 'Application health check failed' }; if ($health.version -ne $env:VERSION) { throw 'Version mismatch' }; if ($health.environment -ne $env:APP_ENV) { throw 'Environment mismatch' }"
                '''

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$db = Invoke-RestMethod http://localhost:$env:HOST_PORT/db-health; Write-Host 'Database health:'; $db | ConvertTo-Json; if ($db.database -ne 'UP') { throw 'Database connectivity check failed' }"
                '''

                bat '''
                    "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$search = Invoke-RestMethod 'http://localhost:'$env:HOST_PORT'/customers/search?name=Chandana'; Write-Host 'Customer search response:'; $search | ConvertTo-Json"
                '''

                echo '========================================'
                echo 'DEPLOYMENT VALIDATION SUCCESSFUL'
                echo '========================================'
            }
        }

        stage('Rollback') {
            when {
                expression {
                    params.ACTION == 'ROLLBACK'
                }
            }

            steps {

                echo 'Rollback action selected.'
                echo 'Rollback mechanism will be implemented after deployment validation.'
            }
        }
    }

    post {

        success {
            echo '========================================'
            echo 'PIPELINE COMPLETED SUCCESSFULLY'
            echo '========================================'
        }

        failure {
            echo '========================================'
            echo 'PIPELINE FAILED'
            echo '========================================'
        }
    }
}