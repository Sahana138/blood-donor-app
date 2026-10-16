pipeline {
    agent any

    options {
        timestamps()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Build backend image') {
            steps {
                sh 'docker build -t blood-backend:ci ./backend'
            }
        }

        stage('Run tests') {
            steps {
                sh 'docker run --rm blood-backend:ci pytest -v'
            }
        }

        stage('Build frontend image') {
            steps {
                sh 'docker build -t blood-frontend:ci ./frontend'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker compose up -d --build'
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    for i in 1 2 3 4 5 6 7 8 9 10; do
                      if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"; then
                        echo "Backend is healthy"
                        exit 0
                      fi
                      echo "Waiting for backend..."
                      sleep 5
                    done
                    echo "Backend did not become healthy"
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline finished: tests passed and app deployed.'
        }
        failure {
            echo 'Pipeline failed. Check the stage that turned red.'
        }
        always {
            sh 'docker image prune -f'
        }
    }
}