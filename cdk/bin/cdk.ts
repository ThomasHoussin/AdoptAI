#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AdoptaiStack } from '../lib/adoptai-stack';
import { AwsSolutionsChecks } from 'cdk-nag';

const app = new cdk.App();

// Get configuration from context (defined in cdk.json)
const domainName = app.node.tryGetContext('domainName');
const hostedZoneDomain = app.node.tryGetContext('hostedZoneDomain');

new AdoptaiStack(app, 'AdoptaiStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1',
  },
  domainName,
  hostedZoneDomain,
});

// Apply CDK Nag for security best practices
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
