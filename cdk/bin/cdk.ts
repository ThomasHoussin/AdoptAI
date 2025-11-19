#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AdoptaiStack } from '../lib/adoptai-stack';
import { AwsSolutionsChecks } from 'cdk-nag';

const app = new cdk.App();

// Get configuration from context
const domainName = app.node.tryGetContext('domainName') || 'adoptai.codecrafter.fr';
const certificateArn = app.node.tryGetContext('certificateArn');

new AdoptaiStack(app, 'AdoptaiStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'eu-west-1',
  },
  domainName,
  certificateArn,
});

// Apply CDK Nag for security best practices
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
