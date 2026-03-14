# Dissafyt Platform-Level System Map (PLSM)

> A comprehensive, strategic map of the Dissafyt platform covering goals, architecture, data model, key flows, MVP scope, and next steps.

---

## 1. Vision & Goals

### 1.1 Vision
Dissafyt aims to be a fast, affordable, low-friction Website-as-a-Service platform tailored to local service businesses (e.g., plumbers, barbers, restaurants). It provides a single backend that can host thousands of customer websites by dynamically rendering template-driven sites from user-provided CMS data.

### 1.2 Key Goals
- Enable non-technical local businesses to launch a professional website within minutes.
- Keep infrastructure simple with a single Django monolith.
- Use a template + CMS data model to minimize per-site customization overhead.
- Support quick onboarding, content management, and site publishing to subdomains, with eventual custom domain support.

---

## 2. High-Level Architecture

### 2.1 Monolithic Django Platform
Dissafyt is a single Django project containing multiple apps. This is a deliberate decision to minimize operational complexity early on.

**Core apps:**
- `marketing/` – public marketing site (lead capture, product pages, pricing, signup)
- `dashboard/` – authenticated client management UI (onboarding wizard, content editing, site settings)
- `cms/` – business/content models, forms, and management APIs
- `websites/` – website instance records, template assignment, rendering logic

### 2.2 Rendering Engine (Dynamic)
Every incoming request is handled by Django. The system:
1. Reads the request host header (`request.get_host()`).
2. Matches host/subdomain to a `Website` record.
3. Loads the assigned template (e.g., `templates/sites/<template>/home.html`).
4. Builds a render context from CMS models (`BusinessProfile`, `Service`, `Testimonial`, `GalleryImage`).
5. Renders HTML and returns the response.

There is **no static site generation**; every request is rendered dynamically.

### 2.3 Hosting & Domain Strategy
- **Subdomain-first:** Customers get `businessname.dissafyt.co.za` by default.
- **Custom domain:** Later phases add DNS + domain mapping to allow `businessname.co.za` (with SSL, routing, and domain verification).

---

## 3. Core Data Model

The CMS is the single source of truth for website content. The key models are:

### 3.1 BusinessProfile
- `owner` (User)
- `business_name`
- `phone`, `email`, `address`
- `description`
- `logo`

### 3.2 Website
- `owner` (User)
- `business_profile` (FK)
- `template_name` (string)
- `subdomain` (string)
- `custom_domain` (string)
- `published` (boolean)

### 3.3 Content Models
- `Service` (name, description)
- `Testimonial` (author, quote)
- `GalleryImage` (image, caption)

These models are used to populate templates at render-time.

---

## 4. User Journeys

### 4.1 Visitor -> Marketing Funnel
1. Visitor lands on marketing site (`/`, `/pricing`, `/templates`, `/contact`).
2. Visitor decides to sign up and is routed to the onboarding flow.

### 4.2 Onboarding → Dashboard → Website
1. User signs up (auth flows). 
2. User enters business details (BusinessProfile) via the onboarding wizard.
3. User selects a website template and personalizes content (services, testimonials, gallery).
4. User publishes the site, which creates/updates a `Website` record with `published=true`.
5. The system makes the site available at `subdomain.dissafyt.co.za`.

### 4.3 Content Updates
1. User updates CMS content (services, testimonials, images).
2. Changes are reflected immediately on the live website (because rendering is dynamic).

---

## 5. Technical Implementation Map

### 5.1 Routing
- Marketing pages: standard Django views and templates under `marketing/`.
- Dashboard pages: views within `dashboard/` and protected by authentication.
- Client sites: middleware or view logic inspects `Host` and dispatches to `websites/` rendering logic.

### 5.2 Templates & Themes
- Templates are stored under `templates/sites/<template_name>/...`.
- Each template expects specific context keys (`business`, `services`, `testimonials`, `gallery`).
- Template switching is handled by changing the `template_name` on the `Website` record.

### 5.3 Media Handling
- Client-uploaded images (logos, galleries) are stored in `media/`.
- Django `MEDIA_URL` and `MEDIA_ROOT` are configured so uploaded content is served correctly.

---

## 6. MVP Roadmap (Aligned to docs/MVP_Roadmap.md)

### Phase 1: Project Setup
- Initialize Django project structure
- Add apps (marketing, dashboard, cms, websites)
- Configure templates, static files, and basic settings

### Phase 2: Marketing Site
- Build homepage, pricing, templates listing, contact page, signup flow
- Capture leads and route traffic to signup

### Phase 3: Authentication
- User signup, login, password reset
- Restrict dashboard to authenticated users

### Phase 4: CMS Models
- Build `BusinessProfile`, `Service`, `Testimonial`, `GalleryImage`
- Add admin CRUD for models + dashboard forms

### Phase 5: Website Engine
- Implement `Website` model, template assignment, subdomain routing
- Ensure dynamic rendering based on request host

### Phase 6: Onboarding Wizard
- Multi-step onboarding: business info → services → images → template → publish
- Persist progress in user session / model state

### Phase 7: Domain Mapping
- Allow customers to map custom domains
- Implement DNS verification + serving via host header + SSL

---

## 7. Key Risks & Assumptions

### 7.1 Risks
- **Performance:** Dynamic rendering could become slow at scale; caching strategy may be needed.
- **Multi-tenancy:** Shared codebase means one misconfiguration could affect all sites.
- **Template security:** Templates must be sandboxed to avoid injection/escape issues.

### 7.2 Assumptions
- Most customers need a simple brochure website (no complex custom logic).
- Content updates should reflect instantly (no build step).
- Customers are OK with a predefined set of templates.

---

## 8. Next Recommended Actions

1. **Inspect current code** to verify DTOs and rendering logic match docs.
2. **Implement or validate onboarding wizard** to ensure users can reach the `published` state.
3. **Add unit/integration tests** covering:
   - Host-to-website resolution
   - Rendering template contexts
   - Onboarding flow state transitions
4. **Prototype custom domain mapping** (DNS validation + SSL).

---

If you want, I can also expand this into a living architecture document that syncs with the actual Django app structure and routes (including view names, URLs, and template paths), or create a high-level diagram (Mermaid) for visual reference.