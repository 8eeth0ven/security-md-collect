# Security notes

## Reporting
Please report suspected vulnerabilities privately to the repository owner rather than opening a public issue.

## Dependency policy
* Every image and the local setup install **hash-pinned locks** (`*/requirements.txt`, `agents/deploy/*.lock`)
  compiled from the hand-written `*.in` inputs by `deploy/scripts/lock.sh` (`make lock`). Nothing resolves
  at build time.
* CVE floors live in the `.in` files (e.g. `starlette>=1.3.1`, `urllib3>=2.8.0`).
* Agent images resolve "as of" a fixed date (`LOCK_DATE`) so the OpenTelemetry/ADOT stack only changes on purpose.

## Accepted risks
| Item | Why accepted | Mitigation | Revisit |
| --- | --- | --- | --- |
| `chromadb 1.5.9` (CVE-2026-45829, -45833, -45830, -45831) in the Order Desk image and local setup | Hard dependency of CrewAI (imported at start-up, required `~=1.5.9` even by CrewAI 1.15.40); 1.5.9 is the latest release. The CVEs are in the Chroma **server** API; NeonByte never runs a Chroma server and uses no CrewAI memory/knowledge features. | The Order Desk image deletes chromadb's `server/`, `app.py`, `cli/` and `test/` (agents/deploy/Dockerfile). | Re-lock as soon as chromadb ships a fix. |
| `aws-marketplace:Subscribe/ViewSubscriptions` on `*` (AgentPolicy) | Amazon Bedrock subscribes the account to third-party models on first invocation by the agent role; Marketplace has no resource-level permissions and a global endpoint. | Read/subscribe only; no unsubscribe or seller actions. | If models are pre-subscribed by the event account owner, drop the statement. |
| Bedrock model access (AgentPolicy) | Limited to the four configured models (template parameters): their inference profiles and foundation models in this Region, plus foundation models in other Regions **only** via those inference profiles (`bedrock:InferenceProfileArn`). | Changing a model parameter updates the policy automatically. | — |
| MemoryRole `bedrock:InvokeModel` on foundation models / inference profiles | AgentCore Memory's built-in summary and user-preference strategies run extraction on AWS-selected models, not the agents' configured models; narrowing to our four models would break long-term memory. | Role is assumable only by `bedrock-agentcore.amazonaws.com` for this account; invoke actions only. | Scope to the strategy models if AWS documents them. |
| AgentPolicy `logs:DescribeLogGroups` on `log-group:*` | AWS-documented AgentCore execution-role permission, called by the AgentCore service; list-level action. | Account- and Region-scoped (resource ARN + `aws:RequestedRegion`); no read access to log events. | — |
| `Resource: "*"` on Describe/telemetry actions (EC2 prefix lists, ELB describe, X-Ray, CloudWatch PutMetricData, ECR GetAuthorizationToken — agents and CodeBuild) | These APIs do not support resource-level permissions. | Each is limited with `aws:RequestedRegion` (PutMetricData also by namespace). | — |

Template rules that conflict with running in AWS event accounts are suppressed per resource in
`deploy/cloudformation/neonbyte.yaml` (`Metadata.guard.SuppressedRules`) with the reason inline.
