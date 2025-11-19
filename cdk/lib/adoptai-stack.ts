import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as logs from 'aws-cdk-lib/aws-logs';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Construct } from 'constructs';
import * as path from 'path';
import { NagSuppressions } from 'cdk-nag';

export interface AdoptaiStackProps extends cdk.StackProps {
  domainName?: string;
  certificateArn?: string;
}

export class AdoptaiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: AdoptaiStackProps) {
    super(scope, id, props);

    const dataBucket = new s3.Bucket(this, 'DataBucket', {
      bucketName: `adoptai-data-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
    });

    new s3deploy.BucketDeployment(this, 'DeployData', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '../../data'))],
      destinationBucket: dataBucket,
      destinationKeyPrefix: 'data',
    });

    // Log group for Lambda
    const logGroup = new logs.LogGroup(this, 'ApiLogGroup', {
      logGroupName: '/aws/lambda/adoptai-api',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const apiFunction = new PythonFunction(this, 'ApiFunction', {
      entry: path.join(__dirname, 'lambda'),
      runtime: lambda.Runtime.PYTHON_3_14,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      architecture: lambda.Architecture.ARM_64,
      environment: {
        BUCKET_NAME: dataBucket.bucketName,
        DATA_PREFIX: 'data',
        POWERTOOLS_SERVICE_NAME: 'adoptai-api',
        POWERTOOLS_LOG_LEVEL: 'INFO',
      },
      logGroup,
    });

    dataBucket.grantRead(apiFunction);

    const version = apiFunction.currentVersion;
    const alias = new lambda.Alias(this, 'ApiAlias', { aliasName: 'live', version });

    const cfnFunction = apiFunction.node.defaultChild as lambda.CfnFunction;
    cfnFunction.addPropertyOverride('SnapStart', { ApplyOn: 'PublishedVersions' });

    const functionUrl = alias.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ['*'],
        allowedMethods: [lambda.HttpMethod.GET],
        allowedHeaders: ['Content-Type', 'Authorization'],
        maxAge: cdk.Duration.hours(1),
      },
    });

    let distribution: cloudfront.Distribution;
    if (props?.certificateArn && props?.domainName) {
      const certificate = acm.Certificate.fromCertificateArn(this, 'Certificate', props.certificateArn);
      distribution = new cloudfront.Distribution(this, 'Distribution', {
        defaultBehavior: {
          origin: new origins.FunctionUrlOrigin(functionUrl),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
        domainNames: [props.domainName],
        certificate,
        minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
        httpVersion: cloudfront.HttpVersion.HTTP2_AND_3,
      });
    } else {
      distribution = new cloudfront.Distribution(this, 'Distribution', {
        defaultBehavior: {
          origin: new origins.FunctionUrlOrigin(functionUrl),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
        minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
        httpVersion: cloudfront.HttpVersion.HTTP2_AND_3,
      });
    }

    NagSuppressions.addResourceSuppressions(dataBucket, [
      { id: 'AwsSolutions-S1', reason: 'Server access logging not required for simple data bucket' },
    ], true);

    NagSuppressions.addResourceSuppressions(apiFunction, [
      { id: 'AwsSolutions-IAM4', reason: 'AWS managed policy for Lambda', appliesTo: ['Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'] },
      { id: 'AwsSolutions-IAM5', reason: 'Lambda needs bucket read access', appliesTo: ['Action::s3:GetBucket*', 'Action::s3:GetObject*', 'Action::s3:List*', 'Resource::<DataBucketE3889A50.Arn>/*'] },
      { id: 'AwsSolutions-L1', reason: 'Python 3.14 is the latest Lambda runtime' },
    ], true);

    NagSuppressions.addResourceSuppressions(distribution, [
      { id: 'AwsSolutions-CFR1', reason: 'Geo restrictions not required' },
      { id: 'AwsSolutions-CFR2', reason: 'WAF not required for read-only API' },
      { id: 'AwsSolutions-CFR3', reason: 'Access logging not required for demo' },
      { id: 'AwsSolutions-CFR4', reason: 'Using TLS 1.2' },
    ], true);

    NagSuppressions.addStackSuppressions(this, [
      { id: 'AwsSolutions-IAM4', reason: 'Auto-generated service roles', appliesTo: ['Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'] },
      { id: 'AwsSolutions-IAM5', reason: 'Custom resources need broad permissions', appliesTo: [
        'Resource::*',
        'Action::s3:GetBucket*',
        'Action::s3:GetObject*',
        'Action::s3:List*',
        'Action::s3:Abort*',
        'Action::s3:DeleteObject*',
        'Resource::<DataBucketE3889A50.Arn>/*',
        { regex: '/^Resource::arn:aws:s3:::cdk-.*/' },
      ]},
      { id: 'AwsSolutions-L1', reason: 'Custom resource runtimes managed by CDK' },
    ]);

    new cdk.CfnOutput(this, 'FunctionUrl', { value: functionUrl.url, description: 'Lambda Function URL' });
    new cdk.CfnOutput(this, 'CloudFrontUrl', { value: `https://${distribution.distributionDomainName}`, description: 'CloudFront URL' });
    new cdk.CfnOutput(this, 'BucketName', { value: dataBucket.bucketName, description: 'S3 Bucket Name' });
    if (props?.domainName) {
      new cdk.CfnOutput(this, 'CustomDomainUrl', { value: `https://${props.domainName}`, description: 'Custom Domain URL' });
    }
  }
}
