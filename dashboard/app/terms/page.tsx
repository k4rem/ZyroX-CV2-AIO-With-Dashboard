import { LegalPageShell } from "@/components/legal/legal-page-shell";

export const metadata = { title: "Terms" };

export default function TermsPage() {
  return (
    <LegalPageShell title="Terms of use">
      <section>
        <h2 className="text-section text-fg-1">Private system</h2>
        <p>
          CLS OS is provided for authorized CLS operators only. Using the dashboard means you act on behalf of a
          Discord server where you have been granted access—not because you hold Discord Administrator by default.
        </p>
      </section>
      <section>
        <h2 className="text-section text-fg-1">Acceptable use</h2>
        <p>
          You may configure bot and platform features only for servers you are authorized to manage. Do not attempt
          to bypass access controls, probe unauthorized APIs, or use the dashboard to harass users or violate
          Discord&apos;s Terms of Service.
        </p>
      </section>
      <section>
        <h2 className="text-section text-fg-1">Availability</h2>
        <p>
          CLS OS depends on the bot service, database, and Discord APIs. Features may change, move between phases,
          or be unavailable during maintenance. There is no public uptime or performance guarantee on this page.
        </p>
      </section>
      <section>
        <h2 className="text-section text-fg-1">Liability</h2>
        <p>
          The software is provided as-is to the extent permitted by applicable law. Operators remain responsible for
          how configuration changes affect their Discord communities.
        </p>
      </section>
    </LegalPageShell>
  );
}
