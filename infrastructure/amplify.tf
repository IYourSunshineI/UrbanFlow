resource "aws_amplify_app" "urbanflow_frontend" {
  name       = "urbanflow-frontend"
  repository = "https://github.com/IYourSunshineI/UrbanFlow"
  branch_name = "infrastructure"

  # The build spec is required for Amplify Gen 2 / Web Compute
  build_spec = <<-EOT
    version: 1
    applications:
      - frontend:
          phases:
            preBuild:
              commands:
                - npm ci
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: dist/urbanflow-frontend
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
        appRoot: urban-flow-frontend
  EOT

  enable_auto_branch_creation = true
  enable_branch_auto_build    = true
  enable_branch_auto_deletion = true
  platform                    = "WEB" 

  # Auto-branch creation config
  auto_branch_creation_config {
    enable_auto_build = true
  }
}

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.urbanflow_frontend.id
  branch_name = "main"

  framework = "Angular"
  stage     = "PRODUCTION"
}
