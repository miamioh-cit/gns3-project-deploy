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
            writeFile file: 'datastore', text: "${params.DATASTORE}"
            writeFile file: 'project-id', text: "${params.PROJECT_ID}"
            
            withCredentials([usernamePassword(credentialsId: 'Backstage-GNS3-Project-Deploy', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                sh """
                    git config user.email "jenkins@miamioh.edu"
                    git config user.name "Jenkins CI"
                    git add datastore project-id
                    // ADDED [skip ci] TO PREVENT JENKINS LOOP
                    git diff --staged --quiet || git commit -m "Deploy project ${params.PROJECT_ID} (IP: ${params.IP_ADDRESS}) [skip ci]"
                    git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/miamioh-cit/gns3-project-deploy.git main
                """
            }
        }
    }
}

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
                rm -rf course-config
                git clone --depth 1 --no-tags --branch main https://${COURSE_USER}:${COURSE_PAT}@github.com/kunkelec-stack/it-ot-security-course.git course-config
                
                docker builder prune -f || true
                docker build --no-cache -t ${IMAGE_NAME}-480 -f Dockerfile .
                
                // EXPLICIT ENTRYPOINT PREVENTS DUAL-RUNS
                docker run --rm \
                  --entrypoint python3 \
                  -e GNS3_URL=http://${params.IP_ADDRESS}:80 \
                  -e GNS3_USER=gns3 \
                  -e GNS3_PASSWORD=gns3 \
                  ${IMAGE_NAME}-480 480-2-build.py
            """
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
