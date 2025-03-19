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

        stage('Check Python & Pip') {
            steps {
                script {
                    sh """
                    which python3 || echo '⚠️ Python3 not found!'
                    which pip3 || echo '⚠️ Pip3 not found!'
                    python3 --version || echo '⚠️ Python3 not installed!'
                    pip3 --version || echo '⚠️ Pip3 not installed!'
                    """
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    sh "python3 -m ensurepip --default-pip || echo '⚠️ ensurepip failed!'"
                    sh "python3 -m pip install --user gns3fy || echo '⚠️ Pip install failed!'"
                }
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
