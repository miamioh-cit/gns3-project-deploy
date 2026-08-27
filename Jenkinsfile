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

        // ==========================================
        // ROUTE 1: STANDARD DEPLOYMENTS
        // Runs for everything EXCEPT 480-2
        // ==========================================
        stage('Build Docker Image (Standard)') {
            when {
                expression { return params.PROJECT_ID != '480-2' }
            }
            steps {
                script {
                    sh "docker builder prune -f || true"
                    sh "docker build --no-cache -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('Run GNS3 Deployment (Standard)') {
            when {
                expression { return params.PROJECT_ID != '480-2' }
            }
            steps {
                script {
                    sh "docker run --rm -e GNS3_URL=http://${params.IP_ADDRESS}:80 ${IMAGE_NAME}"
                }
            }
        }

       // ==========================================
        // ROUTE 2: CUSTOM 480-2 DEPLOYMENT
        // Runs ONLY for 480-2
        // ==========================================
        stage('Deploy Custom Course (480-2)') {
            when {
                expression { return params.PROJECT_ID == '480-2' }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'it-ot-security-course', 
                        usernameVariable: 'COURSE_USER', 
                        passwordVariable: 'COURSE_PAT'
                    )
                ]) {
                    sh """
                        echo "📚 Checking out private course repository..."
                        rm -rf course-config
                        git clone --depth 1 --no-tags --branch main https://${COURSE_USER}:${COURSE_PAT}@github.com/kunkelec-stack/it-ot-security-course.git course-config
                        
                        echo "🐳 Building Docker image for 480-2 using root Dockerfile..."
                        docker builder prune -f || true
                        docker build --no-cache -t ${IMAGE_NAME}-480 -f Dockerfile .
                        
                        echo "🚀 Running GNS3 deployment for 480-2..."
                        docker run --rm \\
                          -e GNS3_URL=http://${params.IP_ADDRESS}:80 \\
                          -e GNS3_USER=gns3 \\
                          -e GNS3_PASSWORD=gns3 \\
                          ${IMAGE_NAME}-480 python3 480-2-build.py
                    """
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
