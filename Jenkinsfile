pipeline {
    agent any

    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        IMAGE_NAME = 'gns3-deploy'
    }

    stages {
        stage('Checkout Main Code') {
             steps {
                git url: "${GITHUB_URL}",
                    branch: 'main',
                    credentialsId: 'Backstage-GNS3-Project-Deploy'
            }
        }
        
        stage('Deploy Custom Course') {
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
                            
                            echo "🐳 Building Docker image..."
                            cd course-config/course_it_ot_convergence/gns3_water_treatment
                            
                            docker builder prune -f || true
                            docker build --no-cache -t ${IMAGE_NAME} .
                            
                            echo "🚀 Running GNS3 deployment via Docker..."
                            docker run --rm \
                              -e GNS3_URL=http://${TARGET_IP}:80 \
                              -e GNS3_USER=gns3 \
                              -e GNS3_PASSWORD=gns3 \
                              ${IMAGE_NAME}
                        '''
                    }
                }
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

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'Backstage-GNS3-Project-Deploy',
                            usernameVariable: 'GIT_USERNAME',
                            passwordVariable: 'GIT_PASSWORD'
                        )
                    ]) {
                        withEnv(["TARGET_IP=${params.IP_ADDRESS}", "PROJ_ID=${params.PROJECT_ID}", "DS=${params.DATASTORE}"]) {
                            sh '''
                                git config user.email "jenkins@miamioh.edu"
                                git config user.name "Jenkins CI"

                                git add datastore project-id

                                git diff --staged --quiet || \
                                git commit -m "Deploy project ${PROJ_ID} to datastore ${DS} (IP: ${TARGET_IP})"

                                git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/miamioh-cit/gns3-project-deploy.git main
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ GNS3 Project ${params.PROJECT_ID} Pipeline Completed for ${params.IP_ADDRESS}!"
        }
        failure {
            echo "❌ GNS3 Project Deployment Failed!"
        }
    }
}
