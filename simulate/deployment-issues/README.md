# Kubernetes Deployment Issue Scenarios

This directory contains scenarios that simulate various deployment-related issues in Kubernetes. These scenarios are designed to test the ability of monitoring and troubleshooting tools to identify common deployment failures.

## Scenarios

### Blue/Green Deployment Service Switch Failure

**File:** [blue-green-switch-failure.yaml](blue-green-switch-failure.yaml)

**Description:** Simulates a common issue in blue/green deployments where the new version (green) is successfully deployed, but the service selector is not updated to point to the new version. As a result, traffic continues to flow to the old version (blue) despite the new version being fully deployed and ready.

**Expected Symptoms:**
- Both Blue and Green deployments show as running and ready
- Service selector still points to the Blue deployment
- Client traffic continues to be served by the old version
- No error messages in logs (making this issue harder to detect)
- Deployment is considered "complete" but new features aren't visible

**Root Cause:** Incomplete deployment process where the service selector update step was skipped or failed.

**Resolution:**
- Update the service selector to point to the Green deployment
- Implement automated verification of traffic routing as part of deployment
- Use a service mesh for more sophisticated traffic management
- Add post-deployment tests to verify correct version is being served

## Testing Instructions

1. Apply the scenario:
   ```bash
   kubectl apply -f simulate/deployment-issues/blue-green-switch-failure.yaml
   ```

2. Observe the symptoms:
   ```bash
   # Check both deployments are running
   kubectl get deployments -n simulation-bluegreen-issues
   
   # Check the service selector (still points to blue)
   kubectl get service bluegreen-service -n simulation-bluegreen-issues -o yaml
   
   # See which version the client is receiving
   kubectl logs client-tester -n simulation-bluegreen-issues
   ```

3. Check the diagnosis job results:
   ```bash
   kubectl logs -n simulation-bluegreen-issues -l job-name=blue-green-diagnosis
   ```

4. Fix the issue:
   ```bash
   kubectl patch service bluegreen-service -n simulation-bluegreen-issues -p '{"spec":{"selector":{"version":"green"}}}'
   ```

5. Verify the fix:
   ```bash
   # Check the service selector (now points to green)
   kubectl get service bluegreen-service -n simulation-bluegreen-issues -o yaml
   
   # See that the client now receives the green version
   kubectl logs client-tester -n simulation-bluegreen-issues --tail=10
   ```

6. Clean up:
   ```bash
   kubectl delete namespace simulation-bluegreen-issues
   ```

## Common Challenges in Deployment Processes

- **Manual Steps:** Deployment processes with manual steps are prone to human error
- **Partial Automation:** When some steps are automated but others are manual
- **Complex Coordination:** Multiple teams or systems involved in deployment process
- **Missing Verification:** Lack of post-deployment validation of service routing
- **Incomplete Rollbacks:** Issues that arise during rollbacks when service routing isn't properly handled
- **Documentation Gaps:** Inadequate documentation of the full deployment process
- **Communication Breakdowns:** Different teams responsible for different parts of the deployment

## Best Practices

- Fully automate the deployment process including service switching
- Implement post-deployment validation of service routing
- Use GitOps approaches for deployment where all configuration changes are versioned together
- Consider service mesh technologies for more sophisticated traffic management
- Implement proper monitoring to quickly detect routing issues
- Create comprehensive deployment runbooks that include all necessary steps
- Use blue/green deployment tools that handle both application deployment and traffic switching 