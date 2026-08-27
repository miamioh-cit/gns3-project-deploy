pipeline {
    agent any
    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        IMAGE_NAME = 'gns3-deploy'
    }
    stages {
        stage('Checkout Code') {
            steps {
                git url: "${GITHUB_URL}", branch: 'main', credentialsId: 'Backstage-GNS3-Project-Deploy'
            }
        }
        stage('Update Deployment Files') {
            steps {
                script {
                    // Update the datastore file with the DATASTORE parameter
                    writeFile file: 'datastore', text: "${params.DATASTORE}"

                    // Update the project-id file with the PROJECT_ID parameter
                    writeFile file: 'project-id', text: "${params.PROJECT_ID}"

                    echo "📝 Updated deployment files:"
                    echo "   - Datastore: ${params.DATASTORE}"
                    echo "   - Project ID: ${params.PROJECT_ID}"
                    echo "   - Target IP: ${params.IP_ADDRESS}"

                    // Commit and push changes using Jenkins credentials
                    withCredentials([usernamePassword(credentialsId: 'Backstage-GNS3-Project-Deploy', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
                            git config user.email "jenkins@miamioh.edu"
                            git config user.name "Jenkins CI"
                            git add datastore project-id
                            git diff --staged --quiet || git commit -m "Deploy project ${params.PROJECT_ID} to datastore ${params.DATASTORE} (IP: ${params.IP_ADDRESS})"
                            git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/miamioh-cit/gns3-project-deploy.git main
                        """
                    }
                }
            }
        }
        stage('Build Docker Image (No Cache)') {
            steps {
                script {
                    // Optional: clean up old layers
                    sh "docker builder prune -f || true"
                    // Rebuild image without using cache
                    sh "docker build --no-cache -t ${IMAGE_NAME} ."
                }
            }
        }
        stage('Run GNS3 Deployment in Docker') {
            steps {
                script {
                    sh "docker run --rm ${IMAGE_NAME}"
                    sh "docker run --rm -e GNS3_URL=http://${params.IP_ADDRESS}:80 ${IMAGE_NAME}"
                }
            }
        }
    }
    post {
        success {
            echo "✅ GNS3 Project ${params.PROJECT_ID} Deployed Successfully to ${params.IP_ADDRESS}!"
        }
        failure {
            echo "❌ GNS3 Project Deployment Failed!"
        }
    }
}
