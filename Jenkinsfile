pipeline {
    agent any

    parameters {
        choice(name: 'ENVIRONMENT', choices: ['DEV', 'UAT', 'PRODUCTION'], description: 'Select deployment environment')
        choice(name: 'ACTION', choices: ['DEPLOY', 'ROLLBACK'], description: 'Select deployment action')
        string(name: 'VERSION', defaultValue: '1.3', description: 'Docker image version')
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
                        error("Invalid VERSION '${params.VERSION}'. Use format such as 1.3")
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
                bat 'ping 127.0.0.1 -n 11 > NUL'
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
                    script {
                        if (params.ENVIRONMENT == 'PRODUCTION') {
                            echo '========================================'
                            echo 'PRODUCTION SAFE DEPLOYMENT'
                            echo '========================================'

                            bat '''
                                docker inspect %APP_NAME% --format="{{.Config.Image}}" > previous-image.txt
                                echo Previous production image:
                                type previous-image.txt
                            '''

                            bat '''
                                docker rm -f customer-app-prod-candidate >nul 2>&1
                                docker run -d --name customer-app-prod-candidate --network %NETWORK_NAME% -p 8084:8080 -e ENVIRONMENT=%APP_ENV% -e VERSION=%VERSION% -e DB_HOST=%DB_CONTAINER% -e DB_USER=%DB_USER% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=customerdb customer-app:%VERSION%
                            '''

                            echo 'New production candidate started on port 8084.'
                            echo 'Old production application remains on port 8083.'
                        } else {
                            bat '''
                                docker rm -f %APP_NAME% >nul 2>&1
                                docker run -d --name %APP_NAME% --network %NETWORK_NAME% -p %HOST_PORT%:8080 -e ENVIRONMENT=%APP_ENV% -e VERSION=%VERSION% -e DB_HOST=%DB_CONTAINER% -e DB_USER=%DB_USER% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=customerdb customer-app:%VERSION%
                            '''
                        }
                    }
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
                script {
                    if (params.ENVIRONMENT == 'PRODUCTION') {
                        echo '========================================'
                        echo 'VALIDATING PRODUCTION CANDIDATE'
                        echo '========================================'

                        try {
                            bat '''
                                docker ps --filter name=customer-app-prod-candidate
                                docker ps --filter name=%DB_CONTAINER%
                                docker network inspect %NETWORK_NAME%
                            '''

                            bat '''
                                curl -f http://localhost:8084/health
                                if errorlevel 1 exit /b 1
                            '''

                            bat '''
                                curl -f http://localhost:8084/health | findstr /C:"UP" /C:"%APP_ENV%" /C:"%VERSION%"
                                if errorlevel 1 exit /b 1
                            '''

                            bat '''
                                curl -f http://localhost:8084/db-health
                                if errorlevel 1 exit /b 1
                            '''

                            bat '''
                                curl -f "http://localhost:8084/customers/search?name=Chandana"
                                if errorlevel 1 exit /b 1
                            '''

                            bat '''
                                curl -f "http://localhost:8084/customers/search?name=Chandana" | findstr /C:"SEARCH_COMPLETED"
                                if errorlevel 1 exit /b 1
                            '''

                            echo '========================================'
                            echo 'CANDIDATE VALIDATION SUCCESSFUL'
                            echo '========================================'
                        } catch (Exception e) {
                            echo '========================================'
                            echo 'CANDIDATE VALIDATION FAILED'
                            echo '========================================'

                            bat '''
                                docker rm -f customer-app-prod-candidate >nul 2>&1
                            '''

                            error('Production candidate validation failed. Old production version remains active.')
                        }
                    } else {
                        bat '''
                            docker ps --filter name=%APP_NAME%
                            docker ps --filter name=%DB_CONTAINER%
                        '''

                        bat '''
                            docker network inspect %NETWORK_NAME%
                        '''

                        bat '''
                            curl -f http://localhost:%HOST_PORT%/health
                            if errorlevel 1 exit /b 1
                        '''

                        bat '''
                            curl -f http://localhost:%HOST_PORT%/health | findstr /C:"UP" /C:"%APP_ENV%" /C:"%VERSION%"
                            if errorlevel 1 exit /b 1
                        '''

                        bat '''
                            curl -f http://localhost:%HOST_PORT%/db-health
                            if errorlevel 1 exit /b 1
                        '''

                        bat '''
                            curl -f http://localhost:%HOST_PORT%/db-health | findstr /C:"UP" /C:"%DB_CONTAINER%"
                            if errorlevel 1 exit /b 1
                        '''

                        bat '''
                            curl -f "http://localhost:%HOST_PORT%/customers/search?name=Chandana"
                            if errorlevel 1 exit /b 1
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
            }
        }

        stage('Switch Production') {
            when {
                expression {
                    params.ACTION == 'DEPLOY' && params.ENVIRONMENT == 'PRODUCTION' && params.RUN_TESTS == 'YES'
                }
            }
            steps {
                script {
                    echo '========================================'
                    echo 'SWITCHING PRODUCTION TO NEW VERSION'
                    echo '========================================'

                    bat '''
                        docker rm -f %APP_NAME%
                    '''

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'customer-db-credentials',
                            usernameVariable: 'DB_USER',
                            passwordVariable: 'DB_PASSWORD'
                        )
                    ]) {
                        bat '''
                            docker run -d --name %APP_NAME% --network %NETWORK_NAME% -p %HOST_PORT%:8080 -e ENVIRONMENT=%APP_ENV% -e VERSION=%VERSION% -e DB_HOST=%DB_CONTAINER% -e DB_USER=%DB_USER% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=customerdb customer-app:%VERSION%
                        '''
                    }

                    bat '''
                        docker rm -f customer-app-prod-candidate >nul 2>&1
                    '''

                    echo 'Production switch completed.'
                }
            }
        }

        stage('Final Production Validation') {
            when {
                expression {
                    params.ACTION == 'DEPLOY' && params.ENVIRONMENT == 'PRODUCTION' && params.RUN_TESTS == 'YES'
                }
            }
            steps {
                bat '''
                    curl -f http://localhost:8083/health
                    if errorlevel 1 exit /b 1

                    curl -f http://localhost:8083/db-health
                    if errorlevel 1 exit /b 1
                '''

                echo '========================================'
                echo 'PRODUCTION DEPLOYMENT SUCCESSFUL'
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
                script {
                    echo '========================================'
                    echo 'ROLLBACK ACTION SELECTED'
                    echo '========================================'

                    if (params.ENVIRONMENT != 'PRODUCTION') {
                        error('Rollback is currently supported for PRODUCTION only.')
                    }

                    bat '''
                        if not exist previous-image.txt (
                            echo No previous production image information found.
                            exit /b 1
                        )

                        set /p PREVIOUS_IMAGE=<previous-image.txt
                        echo Restoring previous production image: %PREVIOUS_IMAGE%
                        docker rm -f %APP_NAME% >nul 2>&1
                    '''

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'customer-db-credentials',
                            usernameVariable: 'DB_USER',
                            passwordVariable: 'DB_PASSWORD'
                        )
                    ]) {
                        bat '''
                            set /p PREVIOUS_IMAGE=<previous-image.txt

                            docker run -d --name %APP_NAME% --network %NETWORK_NAME% -p %HOST_PORT%:8080 -e ENVIRONMENT=%APP_ENV% -e VERSION=%VERSION% -e DB_HOST=%DB_CONTAINER% -e DB_USER=%DB_USER% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=customerdb %PREVIOUS_IMAGE%
                        '''
                    }

                    bat '''
                        ping 127.0.0.1 -n 6 > NUL

                        curl -f http://localhost:8083/health
                        if errorlevel 1 exit /b 1

                        curl -f http://localhost:8083/db-health
                        if errorlevel 1 exit /b 1
                    '''

                    echo '========================================'
                    echo 'ROLLBACK COMPLETED SUCCESSFULLY'
                    echo '========================================'
                }
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