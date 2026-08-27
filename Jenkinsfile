pipeline {
    agent any

    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        IMAGE_NAME = 'gns3-deploy'
    }

    stages {
        stage('Checkout Main Code') {
            steps {
                git url: "${GITHUB_URL}", branch: 'main', credentialsId: 'Backstage-GNS3-Project-Deploy'
            }
        }

        stage('Update Deployment Files') {
            steps {
                script {
                    writeFile file: 'datastore', text: "${params.DATASTORE}"
                    writeFile file: 'project-id', text: "${params.PROJECT_ID}"
                    
                    echo "📝 Updated deployment files:"
                    echo "   - Datastore: ${params.DATASTORE}"
                    echo "   - Project ID: ${params.PROJECT_ID}"
                    echo "   - Target IP: ${params.IP_ADDRESS}"
                    
                    withCredentials([usernamePassword(credentialsId: 'Backstage-GNS3-Project-Deploy', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        withEnv(["PROJ_ID=${params.PROJECT_ID}", "DS=${params.DATASTORE}", "TARGET_IP=${params.IP_ADDRESS}"]) {
                            sh '''
                                git config user.email "jenkins@miamioh.edu"
                                git config user.name "Jenkins CI"
                                git add datastore project-id
                                git diff --staged --quiet || git commit -m "Deploy project ${PROJ_ID} to datastore ${DS} (IP: ${TARGET_IP})"
                                git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/miamioh-cit/gns3-project-deploy.git main
                            '''
                        }
                    }
                }
            }
        }

        // ==========================================
        // ROUTE 1: CUSTOM DEPLOYMENT (ONLY FOR 480-2)
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
                    withEnv(["TARGET_IP=${params.IP_ADDRESS}"]) {
                        sh '''
                            echo "📚 Checking out private course repository..."
                            rm -rf course-config
                            git clone --depth 1 --no-tags --branch main https://${COURSE_USER}:${COURSE_PAT}@github.com/kunkelec-stack/it-ot-security-course.git course-config
                            
                            echo "🐳 Building Docker image for 480-2..."
                            cd course-config/course_it_ot_convergence/gns3_water_treatment
                            docker builder prune -f || true
                            docker build --no-cache -t ${IMAGE_NAME}-480 .
                            
                            echo "🚀 Running GNS3 deployment via Docker..."
                            docker run --rm \
                              -e GNS3_URL=http://${TARGET_IP}:80 \
                              -e GNS3_USER=gns3 \
                              -e GNS3_PASSWORD=gns3 \
                              ${IMAGE_NAME}-480
                        '''
                    }
                }
            }
        }

        // ==========================================
        // ROUTE 2: STANDARD DEPLOYMENT (ALL OTHERS)
        // ==========================================
        stage('Deploy Standard Topologies') {
            when {
                expression { return params.PROJECT_ID != '480-2' }
            }
            steps {
                script {
                    echo "🐳 Building standard Docker image..."
                    sh "docker builder prune -f || true"
                    sh "docker build --no-cache -t ${IMAGE_NAME} ."
                    
                    echo "🚀 Running standard GNS3 deployment..."
                    withEnv(["TARGET_IP=${params.IP_ADDRESS}"]) {
                        // Using your original standard run command here
                        sh '''
                            docker run --rm -e GNS3_URL=http://${TARGET_IP}:80 ${IMAGE_NAME}
                        '''
                    }
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
