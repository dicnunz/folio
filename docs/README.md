# Senior Project Website

This project website lives in the `docs/` folder and is intended for GitHub Pages hosting from the `main` branch using the `/docs` publishing source.

## Update the placeholders

Replace the visible placeholder values in `docs/index.html` with the actual project details before publishing: `DUE DATE TBD`

## Add milestone documents

Place milestone files in the appropriate folders under `docs/documents/`.

Recommended naming convention:

- `project-plan.pdf`
- `requirements.pdf`
- `design.pdf`
- `testing.pdf`
- `presentation.pdf`
- `progress-evaluation.pdf`
- `poster.pdf`
- `user-manual.pdf`
- `developer-manual.pdf`
- `demo-video.mp4`

Use lowercase filenames with hyphens and no spaces.

## Convert a “Coming soon” placeholder into a working link

When a document is ready, replace the placeholder text with a proper link using a relative path such as:

- `documents/first-semester/milestone-1/requirements.pdf`
- `documents/first-semester/project-plan/project-plan.pdf`
- `documents/second-semester/milestone-6/demo-video.mp4`

Keep the surrounding HTML comment as a reminder of where the link belongs.

## Preview the site locally

Open `docs/index.html` in a browser to review the page without a build step. If preferred, we can also serve the folder with a simple local static server, but the site is designed to work as a plain static HTML page.

## Publish with GitHub Pages

To publish/update this working project site we must:

1. Commit the changes to the `main` branch.
2. In the GitHub repository settings, choose GitHub Pages.
3. Set the source to `Deploy from a branch`.
4. Select the `main` branch and the `/docs` folder.
5. Save the settings and wait for the site to publish.

## Keep information appropriate for a public site

This website is public so it can work with GitHub Pages. We should not publish our private information, personal contact details beyond school email addresses, or anything sensitive. Keep the content limited to project information, milestones, and public deliverables.
