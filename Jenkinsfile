pipeline {
    agent any

    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git url: "${GITHUB_URL}", branch: 'main'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Run Code') {
            steps {
                script {
                    sh "python3 gns3-project-deploy.py || exit 1"
                }
            }
        }
    }

    post {
        success {
            echo "✅ Update Successful!"
        }
        failure {
            echo "❌ Update Failed!"
        }
    }
}
