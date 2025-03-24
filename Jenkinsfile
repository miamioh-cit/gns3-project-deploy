pipeline {
    agent any

    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        IMAGE_NAME = 'gns3-deploy'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git url: "${GITHUB_URL}", branch: 'main'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('Run GNS3 Deployment in Docker') {
            steps {
                script {
                    sh "docker run --rm ${IMAGE_NAME}"
                }
            }
        }
    }

    post {
        success {
            echo "✅ GNS3 Project Deployed Successfully!"
        }
        failure {
            echo "❌ GNS3 Project Deployment Failed!"
        }
    }
}
