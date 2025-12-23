resource "aws_s3_bucket" "angular_host" {
  bucket = "urban-flow-frontend-local"
}

resource "aws_s3_bucket_website_configuration" "angular_config" {
  bucket = aws_s3_bucket.angular_host.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.angular_host.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.angular_host.arn}/*"
      },
    ]
  })
}