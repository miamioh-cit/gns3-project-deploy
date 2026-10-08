pipeline {
    agent any

    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        IMAGE_NAME = 'gns3-deploy'

        FRESHWATER_SCADA_IMAGE = 'evankunkel/generic-scada-freshwater:latest'
        TRAFFIC_SCADA_IMAGE = 'evankunkel/generic-scada-traffic:latest'
        MANAFACTURING_SCADA_IMAGE = 'evankunkel/generic-scada-manafacturing:latest'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git(
                    url: "${GITHUB_URL}",
                    branch: 'main',
                    credentialsId: 'Backstage-GNS3-Project-Deploy'
                )
            }
        }

        stage('Update Deployment Files') {
            steps {
                script {
                    writeFile file: 'datastore', text: "${params.DATASTORE}"
                    writeFile file: 'project-id', text: "${params.PROJECT_ID}"

                    echo 'Updated deployment files:'
                    echo "  - Datastore: ${params.DATASTORE}"
                    echo "  - Project IDs: ${params.PROJECT_ID}"
                    echo "  - Target IP: ${params.IP_ADDRESS}"

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'Backstage-GNS3-Project-Deploy',
                            usernameVariable: 'GIT_USERNAME',
                            passwordVariable: 'GIT_PASSWORD'
                        )
                    ]) {
                        sh """
                            git config user.email "jenkins@miamioh.edu"
                            git config user.name "Jenkins CI"

                            git add datastore project-id

                            if ! git diff --staged --quiet; then
                                git commit -m "Deploy project ${params.PROJECT_ID} to datastore ${params.DATASTORE} (IP: ${params.IP_ADDRESS}) [skip ci]"
                                git push https://\${GIT_USERNAME}:\${GIT_PASSWORD}@github.com/miamioh-cit/gns3-project-deploy.git main
                            fi
                        """
                    }
                }
            }
        }

        stage('Prepare and Deploy Selected Projects') {
            steps {
                script {
                    // PROJECT_ID can contain one ID or several IDs, one per line.
                    def projectIds = params.PROJECT_ID
                        .readLines()
                        .collect { it.trim() }
                        .findAll { it }

                    if (!projectIds) {
                        error('No project IDs were supplied.')
                    }

                    // Add new custom SCADA projects here instead of adding a new stage.
                    def scadaProjects = [
                        '480-2': [
                            image: env.FRESHWATER_SCADA_IMAGE,
                            dockerfile: 'scada/Dockerfile'
                        ],
                        '480-3': [
                            image: env.TRAFFIC_SCADA_IMAGE,
                            dockerfile: 'scada/traffic/Dockerfile'
                        ],
                        '480-4': [
                            image: env.MANAFACTURING_SCADA_IMAGE,
                            dockerfile: 'scada/manufacturing/Dockerfile'
                        ]
                    ]

                    def selectedScadaProjects = projectIds
                        .findAll { scadaProjects.containsKey(it) }
                        .unique()

                    echo "Selected projects: ${projectIds.join(', ')}"

                    /*
                     * The main Dockerfile always copies course-config, so this
                     * repository must be cloned for every deployment—not just
                     * 480 deployments.
                     */
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'it-ot-security-course',
                            usernameVariable: 'COURSE_USER',
                            passwordVariable: 'COURSE_PAT'
                        )
                    ]) {
                        sh """
                            rm -rf course-config

                            git clone \\
                                --depth 1 \\
                                --no-tags \\
                                --branch main \\
                                https://\${COURSE_USER}:\${COURSE_PAT}@github.com/kunkelec-stack/it-ot-security-course.git \\
                                course-config
                        """
                    }

                    /*
                     * Only build and push SCADA images for the selected custom
                     * projects. Standard projects simply skip this block.
                     */
                    if (selectedScadaProjects) {
                        echo "Preparing SCADA images for: ${selectedScadaProjects.join(', ')}"

                        withCredentials([
                            usernamePassword(
                                credentialsId: 'wtaylor8-dockerhub',
                                usernameVariable: 'DOCKER_USERNAME',
                                passwordVariable: 'DOCKER_TOKEN'
                            )
                        ]) {
                            sh """
                                echo "\${DOCKER_TOKEN}" | docker login \\
                                    --username "\${DOCKER_USERNAME}" \\
                                    --password-stdin
                            """

                            try {
                                selectedScadaProjects.each { projectId ->
                                    def config = scadaProjects[projectId]

                                    echo "Building and pushing SCADA image for ${projectId}"

                                    sh """
                                        docker build \\
                                            --no-cache \\
                                            -t ${config.image} \\
                                            -f ${config.dockerfile} \\
                                            .

                                        docker push ${config.image}
                                    """
                                }
                            } finally {
                                sh 'docker logout || true'
                            }
                        }
                    } else {
                        echo 'No custom SCADA images are needed for the selected projects.'
                    }

                    // One shared deployment image and one shared runner.
                    sh 'docker builder prune -f || true'
                    sh "docker build --no-cache -t ${env.IMAGE_NAME} ."

                    sh """
                        docker run --rm \\
                            -e GNS3_URL=http://${params.IP_ADDRESS}:80 \\
                            -e GNS3_USER=gns3 \\
                            -e GNS3_PASSWORD=gns3 \\
                            ${env.IMAGE_NAME}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "GNS3 project(s) ${params.PROJECT_ID} deployed successfully to ${params.IP_ADDRESS}."
        }

        failure {
            echo 'GNS3 project deployment failed.'
        }
    }
}
