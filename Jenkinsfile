pipeline {
    agent any

    parameters {
        choice(name: 'ENVIRONMENT', choices: ['DEV', 'UAT', 'PRODUCTION'], description: 'Select deployment environment')
        choice(name: 'ACTION', choices: ['DEPLOY', 'ROLLBACK'], description: 'Select deployment action')
        string(name: 'VERSION', defaultValue: '1.2', description: 'Docker image version')
        choice(name: 'RUN_TESTS', choices: ['YES', 'NO'], description: 'Run application validation tests')
        choice(name: 'CONFIRM_PROD', choices: ['NO', 'YES'], description: 'Required for production deployment')
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
                bat 'docker build -t customer-app:%VERSION% .'
                bat 'docker images customer-app:%VERSION%'
            }
        }

        stage('Ensure Docker Network') {
            steps {
                bat '''
                    docker network inspect %NETWORK_NAME% >nul 2>&1
                    if errorlevel 1 docker network create %NETWORK_NAME%
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
                        docker inspect %DB_CONTAINER% >nul 2>&1
                        if errorlevel 1 docker run -d --name %DB_CONTAINER% --network %NETWORK_NAME% -e MYSQL_ROOT_PASSWORD=%DB_PASSWORD% -e MYSQL_DATABASE=customerdb -v %DB_VOLUME%:/var/lib/mysql mysql:8.0
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
                bat 'timeout /t 10 /nobreak >nul'
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
                        docker rm -f %APP_NAME% >nul 2>&1
                        docker run -d --name %APP_NAME% --network %NETWORK_NAME% -p %HOST_PORT%:8080 -e ENVIRONMENT=%APP_ENV% -e VERSION=%VERSION% -e DB_HOST=%DB_CONTAINER% -e DB_USER=%DB_USER% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=customerdb customer-app:%VERSION%
                    '''
                }
            }
        }

        stage('Validate Deployment') {
            when {
                expression {
                    params.ACTION == 'DEPLOY' && params.RUN_TESTS == 'YES'
                }
            }
            steps {

                bat '''
                    echo Checking application container
                    docker ps --filter name=%APP_NAME%

                    echo Checking database container
                    docker ps --filter name=%DB_CONTAINER%
                '''

                bat '''
                    echo Checking Docker network
                    docker network inspect %NETWORK_NAME%
                '''

                bat '''
                    timeout /t 5 /nobreak >nul
                    curl -f http://localhost:%HOST_PORT%/health
                '''

                bat '''
                    curl -f http://localhost:%HOST_PORT%/health | findstr /C:"UP" /C:"%APP_ENV%" /C:"%VERSION%"
                    if errorlevel 1 exit /b 1
                '''

                bat '''
                    echo Checking database connectivity
                    curl -f http://localhost:%HOST_PORT%/db-health
                '''

                bat '''
                    curl -f http://localhost:%HOST_PORT%/db-health | findstr /C:"UP" /C:"%DB_CONTAINER%"
                    if errorlevel 1 exit /b 1
                '''

                bat '''
                    echo Checking customer search feature
                    curl -f "http://localhost:%HOST_PORT%/customers/search?name=Chandana"
                '''

                bat '''
                    curl -f "http://localhost:%HOST_PORT%/customers/search?name=Chandana" | findstr /C:"SEARCH_COMPLETED"
                    if errorlevel 1 exit /b 1
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