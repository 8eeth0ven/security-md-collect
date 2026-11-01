# Security Policy: CUDA-Q Academic

## Reporting a Vulnerability

If you discover a potential security vulnerability in CUDA-Q Academic, please
**do not open a public issue, pull request, or discussion**. Report it privately
through one of these channels:

- **Web (preferred):** [NVIDIA Vulnerability Disclosure Program](https://www.nvidia.com/en-us/security/)
- **Email:** [psirt@nvidia.com](mailto:psirt@nvidia.com). For sensitive email,
  use the [NVIDIA public PGP key](https://www.nvidia.com/en-us/security/pgp-key).
- **Repository:** Use the GitHub or GitLab **Security** tab and select
  **Report a vulnerability**, when private vulnerability reporting is enabled.

Please include:

- The project name and affected version, branch, or commit
- The vulnerability type and affected notebook, helper, widget, or CI path
- Step-by-step reproduction instructions
- Proof-of-concept code, logs, or screenshots, if available
- The expected impact and relevant execution environment

Detailed reports help NVIDIA evaluate and address issues faster. NVIDIA's
Product Security Incident Response Team (PSIRT) will acknowledge the report,
validate and assess the issue, coordinate a fix, and publish a security bulletin
when appropriate.

## Supported Versions

CUDA-Q Academic is maintained as a rolling educational curriculum. Security
updates are applied to the current default branch. Historical commits, copied
notebooks, downloaded archives, and downstream forks are not independently
supported; reproduce reports against the current default branch when possible.

## Security Architecture & Context

CUDA-Q Academic is an externally distributed collection of Jupyter notebooks,
Python helper modules, static visualization widgets, images, sample data, and
curriculum metadata. It teaches quantum computing with CUDA-Q and is not the
CUDA-Q product library, an API service, an authentication system, or a data
storage service.

This software operates at the educational application and content level. Its
primary security responsibility is to preserve the provenance and integrity of
executable lesson content and to document when lessons interact with local
files, third-party packages, hosted models, or external APIs. A notebook kernel
executes code with the permissions of the user or CI runner, so the repository
itself is not a sandbox or privilege boundary.

**Repository Exposure Classification:** Public.

Basis: the project is described and distributed as open-source through a public
NVIDIA GitHub repository and GitHub Pages site; this document uses public-safe
detail.

**Service Exposure Classification:** External / Regulated (high confidence).

Basis: the curriculum and widgets are externally distributed to students and
educators. The repository does not define a production network service and is
not intended to process sensitive data. This is a program-context description,
not a vulnerability-severity rating.

The principal interfaces and trust boundaries are:

- **Jupyter execution:** Student and solution notebooks execute Python, shell
  commands, CUDA-Q kernels, and helper modules on local, hosted, or cloud
  notebook environments.
- **Local files and outputs:** Lessons read bundled images, JSON, NPZ, chemistry,
  and other sample files and may write notebook outputs or generated data.
- **External dependencies and content:** Notebook setup cells can install Python
  packages or download repository files, datasets, and model artifacts. Some
  static HTML widgets load JavaScript and fonts from public content-delivery
  networks.
- **Hosted APIs and credentials:** Calibration notebooks send user-selected
  plots and prompts to an NVIDIA-hosted API using an API key supplied through an
  environment variable or password widget. AI lessons may use a Hugging Face
  access token when downloading a model.
- **Continuous integration:** `.gitlab-ci.yml` installs dependencies and executes
  selected solution notebooks in place, publishes executed notebooks as job
  artifacts, and imports a reusable pipeline-analysis template.
- **Static hosting:** The public learning-path and visualization-gallery pages
  are deployed separately from the `widgets-as-html` branch. This repository's
  default branch contains the curriculum source and only a subset of hosted
  widget files.

### Threat Model

The main security concerns for this repository are:

1. **Contributor-controlled notebook execution in CI:** `.gitlab-ci.yml` executes
   selected solution notebooks with `jupyter nbconvert --execute --inplace`.
   A malicious or compromised notebook or imported helper could run commands
   with the CI runner's permissions, access available environment data, modify
   generated notebooks, or place sensitive content in uploaded artifacts.

2. **Dependency and build-input compromise:** CI uses a container image without
   an explicit immutable digest, installs multiple Python packages at job time,
   and imports a reusable CI template. Notebook setup cells also install
   packages and, in several lessons, download files from a mutable default
   branch. Compromise or unexpected changes in any of these upstream inputs
   could execute code in a learner or CI environment.

3. **Credential or user-data disclosure from notebook execution:**
   `calibration/ising_calibration_intro.ipynb` reads `NVIDIA_API_KEY` from the
   environment, while `calibration/Calibration_Resources_Guide.ipynb` accepts an
   API key and image through widgets. Modified cells, untrusted notebook
   extensions, verbose errors, or saved outputs could disclose credentials or
   transmit a plot somewhere other than the documented API endpoint. The
   `ai-for-quantum` lesson may similarly access `HF_TOKEN`.

4. **Unverified external model and data artifacts:** The AI lesson downloads a
   Hugging Face diffusion model, and the QEC decoder lesson downloads and
   decompresses release data. These paths rely on HTTPS and upstream hosting but
   do not independently verify a cryptographic checksum in the lesson. A changed
   artifact can affect lesson integrity, consume excessive local resources, or
   expose a vulnerability in a downstream parser or model loader.

5. **Third-party JavaScript in visualization widgets:** HTML files such as
   `chemistry-simulations/Images/adapt_vqe/adapt_widget.html` and
   `qec101/Images/MSD/bloch_sphere.html` load scripts from public CDNs without
   Subresource Integrity metadata; some URLs are not version-pinned. A
   compromised or unexpectedly changed CDN response would execute in the
   widget's browser context and could alter displayed educational content.

6. **Resource exhaustion and unsafe execution environments:** Quantum
   simulation, model training, dataset decompression, and high-shot workloads
   can consume substantial CPU, GPU, memory, storage, or API quota. Running
   notebooks on shared or insufficiently isolated systems can degrade
   availability for other users or expose files available to the notebook
   process.

### Critical Security Assumptions

- Users and instructors obtain notebooks from a trusted repository revision,
  review executable cells, and run them in an appropriately isolated
  environment. Opening a notebook for inspection is not equivalent to safely
  executing it.
- CI runners used for merge requests are isolated and do not expose protected
  credentials or privileged infrastructure to untrusted notebook changes.
- The configured container registry, Python package indexes, external model and
  dataset hosts, reusable CI configuration, DNS, and TLS trust store are
  trustworthy. The repository does not provide end-to-end artifact signing or
  checksum verification for every downloaded input.
- API keys and cloud credentials are least-privileged, short-lived where
  practical, supplied at runtime, and never committed to notebooks or saved in
  notebook outputs. Users approve plots and prompts before sending them to a
  hosted API.
- Bundled sample data and learner-provided inputs are non-sensitive and of
  reasonable size. The notebooks are not designed as a secure parser for
  adversarial files or as a system for handling personal, confidential, or
  regulated information.
- Static hosting and third-party browser dependencies are delivered over HTTPS,
  and browsers enforce their normal origin and sandboxing controls. The widgets
  do not implement authentication or authorization boundaries.
- The host operating system, Jupyter server, CUDA-Q installation, GPU drivers,
  cloud notebook platform, and any selected quantum backend enforce their own
  access control, isolation, quota, and update policies.

## Deployment and Usage Guidance

- Treat notebooks and helper scripts as executable software. Review changes
  before running them, especially shell commands, package installation cells,
  downloads, and imported local modules.
- Use a dedicated virtual environment, container, or disposable notebook
  instance. Do not run lessons with elevated operating-system privileges.
- Keep API keys out of cells, source control, screenshots, and saved outputs.
  Rotate a key immediately if it may have been exposed.
- Use trusted, current CUDA-Q and dependency versions. Where reproducibility or
  higher assurance is required, pin packages, container digests, models, and
  downloaded data and verify their checksums.
- Do not place confidential calibration plots or other sensitive files in a
  hosted notebook or send them to an external API unless that use is authorized.
- Configure CI so untrusted contributions cannot access protected variables,
  privileged runners, or long-lived credentials, and review executed-notebook
  artifacts before sharing them.

## Scope

Reports are in scope when they demonstrate a security impact caused by content
maintained in this repository, including notebooks, Python helpers, static
widgets, curriculum metadata, or CI configuration. Vulnerabilities in CUDA-Q,
third-party packages, cloud notebook platforms, hosted model services, or
quantum backends should also be reported to the responsible upstream project;
please report here when this repository's integration or guidance creates an
additional exploitable condition.
