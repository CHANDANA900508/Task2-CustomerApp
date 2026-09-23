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
            description: 'Production deployment confirmation'
        )
    }

    environment {
        IMAGE_NAME = 'customer-app'
        DB_CREDENTIALS_ID = 'customer-db-credentials'
    }

    stages {

        stage('Resolve Configuration') {
            steps {
                script {

                    if (params.ENVIRONMENT == 'DEV') {
                        env.GIT_BRANCH_NAME = 'develop'
                        env.APP_NAME = 'customer-app-dev'
                        env.DB_NAME_CONTAINER = 'customer-db-dev'
                        env.NETWORK_NAME = 'customer-dev-net'
                        env.HOST_PORT = '8081'
                        env.APP_ENV = 'DEV'
                        env.DB_VOLUME = 'customer-db-dev-data'

                    } else if (params.ENVIRONMENT == 'UAT') {
                        env.GIT_BRANCH_NAME = 'release'
                        env.APP_NAME = 'customer-app-uat'
                        env.DB_NAME_CONTAINER = 'customer-db-uat'
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
                        env.DB_NAME_CONTAINER = 'customer-db-prod'
                        env.NETWORK_NAME = 'customer-prod-net'
                        env.HOST_PORT = '8083'
                        env.APP_ENV = 'PRODUCTION'
                        env.DB_VOLUME = 'customer-db-prod-data'

                    } else {
                        error('Invalid environment selected')
                    }

                    echo """
                    ========================================
                    RESOLVED DEPLOYMENT CONFIGURATION
                    ========================================
                    Environment : ${env.APP_ENV}
                    Git Branch  : ${env.GIT_BRANCH_NAME}
                    Action      : ${params.ACTION}
                    Version     : ${params.VERSION}
                    App         : ${env.APP_NAME}
                    Database    : ${env.DB_NAME_CONTAINER}
                    Network     : ${env.NETWORK_NAME}
                    Host Port   : ${env.HOST_PORT}
                    DB Volume   : ${env.DB_VOLUME}
                    Run Tests   : ${params.RUN_TESTS}
                    ========================================
                    """
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
                    if (!(params.VERSION ==~ /^[0-9]+\\.[0-9]+$/)) {
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
                powershell """
                    docker build -t ${env.IMAGE_NAME}:${params.VERSION} .
                    docker images ${env.IMAGE_NAME}:${params.VERSION}
                """
            }
        }

        stage('Ensure Docker Network') {
            steps {
                powershell """
                    docker network inspect ${env.NETWORK_NAME} 2>\\$null
                    if (\\$LASTEXITCODE -ne 0) {
                        docker network create ${env.NETWORK_NAME}
                    }
                """
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
                        credentialsId: "${DB_CREDENTIALS_ID}",
                        usernameVariable: 'DB_USER',
                        passwordVariable: 'DB_PASSWORD'
                    )
                ]) {
                    powershell """
                        docker inspect ${env.DB_NAME_CONTAINER} 2>\\$null

                        if (\\$LASTEXITCODE -ne 0) {
                            docker run -d `
                              --name ${env.DB_NAME_CONTAINER} `
                              --network ${env.NETWORK_NAME} `
                              --network-alias ${env.DB_NAME_CONTAINER} `
                              -e MYSQL_ROOT_PASSWORD=\\$env:DB_PASSWORD `
                              -e MYSQL_DATABASE=customerdb `
                              -v ${env.DB_VOLUME}:/var/lib/mysql `
                              mysql:8.0
                        }
                    """
                }
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
                        credentialsId: "${DB_CREDENTIALS_ID}",
                        usernameVariable: 'DB_USER',
                        passwordVariable: 'DB_PASSWORD'
                    )
                ]) {
                    powershell """
                        docker rm -f ${env.APP_NAME} 2>\\$null

                        docker run -d `
                          --name ${env.APP_NAME} `
                          --network ${env.NETWORK_NAME} `
                          -p ${env.HOST_PORT}:8080 `
                          -e ENVIRONMENT=${env.APP_ENV} `
                          -e VERSION=${params.VERSION} `
                          -e DB_HOST=${env.DB_NAME_CONTAINER} `
                          -e DB_USER=\\$env:DB_USER `
                          -e DB_PASSWORD=\\$env:DB_PASSWORD `
                          -e DB_NAME=customerdb `
                          ${env.IMAGE_NAME}:${params.VERSION}
                    """
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
                powershell """
                    Write-Host "Checking application container..."
                    docker ps --filter "name=${env.APP_NAME}"

                    Write-Host "Checking database container..."
                    docker ps --filter "name=${env.DB_NAME_CONTAINER}"

                    Write-Host "Checking Docker network..."
                    docker network inspect ${env.NETWORK_NAME}

                    Write-Host "Checking application health..."
                    Start-Sleep -Seconds 5

                    Invoke-RestMethod `
                      -Uri "http://localhost:${env.HOST_PORT}/health"

                    Write-Host "Checking database connectivity..."
                    Invoke-RestMethod `
                      -Uri "http://localhost:${env.HOST_PORT}/db-health"

                    Write-Host "Checking customer search..."
                    Invoke-RestMethod `
                      -Uri "http://localhost:${env.HOST_PORT}/customers/search?name=Chandana"

                    Write-Host "Checking deployed version..."
                    \\$health = Invoke-RestMethod `
                      -Uri "http://localhost:${env.HOST_PORT}/health"

                    if (\\$health.version -ne "${params.VERSION}") {
                        throw "Version mismatch. Expected ${params.VERSION}, found \\$($health.version)"
                    }

                    if (\\$health.environment -ne "${env.APP_ENV}") {
                        throw "Environment mismatch. Expected ${env.APP_ENV}, found \\$($health.environment)"
                    }

                    Write-Host "DEPLOYMENT VALIDATION SUCCESSFUL"
                """
            }
        }

        stage('Rollback') {
            when {
                expression {
                    params.ACTION == 'ROLLBACK'
                }
            }

            steps {
                echo "Rollback action selected."
                echo "Rollback implementation will restore the previous production image."
            }
        }
    }

    post {
        success {
            echo "========================================"
            echo "PIPELINE COMPLETED SUCCESSFULLY"
            echo "========================================"
        }

        failure {
            echo "========================================"
            echo "PIPELINE FAILED"
            echo "========================================"
        }
    }
}