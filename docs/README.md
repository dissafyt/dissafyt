# Dissafyt Documentation Overview

This `docs/` directory contains the core design and architecture notes for the Dissafyt platform.

> **Note:** As requested, this overview ignores `7. 1000_Prompts_to_Completion.md`.

---

## 📌 What Dissafyt Is

Dissafyt is a **Website-as-a-Service platform** built on a single Django codebase that dynamically renders many client websites from a shared backend.

Key themes:
- Single Django monolith for all functionality
- Client websites are generated from templates + CMS data
- Subdomains are used by default (e.g., `businessname.dissafyt.co.za`)
- Custom domains can be mapped later

---

## 🧩 Core Documentation in `docs/`

### 1. System Overview (`1. System_Overview.md`)
Describes the platform goals and target users, and outlines the full flow:
- Visitor arrives at marketing site
- Client signs up and completes onboarding
- CMS data is stored
- Template is selected and rendered
- Website is published to a subdomain (and later custom domain)

### 2. System Architecture (`2. System_Architecture.md`)
Explains the monolithic Django architecture and the main components:
- **Marketing Website** (public pages, lead capture)
- **Client Dashboard** (onboarding + site management)
- **CMS Data Layer** (stores business info, services, gallery, etc.)
- **Website Rendering Engine** (dynamic template rendering based on request host)

It also describes the request flow (host header → website record → template → render).

### 3. Data Model (`3. Data_Model.md`)
Defines the key models used for powering websites:
- `BusinessProfile` (owner, contact info, logo, description)
- `Website` (template, subdomain/custom domain, publish state)
- `Service`, `Testimonial`, `GalleryImage` (content types used to populate templates)

### 4. File/Directory Architecture (`4. File_Directory_Architecture.md`)
Maps the Django project layout and where key pieces live:
- `dissafyt_platform/` with `config/`, `apps/`, `templates/`, `static/`, `media/`
- App boundaries: `marketing`, `dashboard`, `cms`, `websites`
- Template conventions (e.g., `templates/sites/<template>/home.html`)

### 5. Client Website Rendering Logic (`5. Client_Website_Rendering_Logic.md`)
Describes the runtime flow for serving a client site:
1. User visits a (sub)domain
2. System reads `request.get_host()`
3. Lookup `Website` record
4. Load the assigned template
5. Inject CMS data (`business`, `services`, `testimonials`, `gallery`)
6. Render and return HTML

### 6. MVP Roadmap (`6. MVP_Roadmap.md`)
Lists the phases of core functionality, from initial project setup through marketing pages, authentication, CMS models, site rendering, onboarding wizard, and custom domain mapping.

---

## ✅ What to Know Going Forward

- The platform is built to be **data-first**: content comes from a CMS model, and websites are generated on every request.
- The codebase is organized around a **monolithic Django project** with clear app boundaries.
- The **Client Dashboard** and **rendering engine** are tightly coupled via shared models (e.g., `Website`, `BusinessProfile`).
- The next development areas likely revolve around:
  - completing onboarding flow (wizard + data collection)
  - implementing template selection + rendering
  - mapping custom domains and handling routing

---

If you want, I can also generate a high-level diagram or extract an explicit list of models/endpoints from the codebase based on the current implementation.