import { LegalPageShell } from "@/components/legal/legal-page-shell";

export const metadata = { title: "Privacy" };

export default function PrivacyPage() {
  return (
    <LegalPageShell title="Privacy">
      <section>
        <h2 className="text-section text-fg-1">What CLS OS is</h2>
        <p>
          CLS OS is a private web dashboard used to configure and operate CLS Discord bot and platform services.
          Access is limited to accounts granted by the CLS owner.
        </p>
      </section>
      <section>
        <h2 className="text-section text-fg-1">Information we process</h2>
        <ul className="list-disc space-y-2 ps-5">
          <li>
            <strong className="font-medium text-fg-1">Discord sign-in:</strong> When you sign in, we request the
            Discord OAuth <span className="cls-mono-data">identify</span> scope to read your Discord user ID,
            username, and avatar for session display.
          </li>
          <li>
            <strong className="font-medium text-fg-1">Dashboard sessions:</strong> The backend creates a dashboard
            session tied to your Discord identity so API requests can be authorized.
          </li>
          <li>
            <strong className="font-medium text-fg-1">Configuration data:</strong> Settings you save (moderation,
            tickets, welcome, roles, and similar module configuration) are stored for the Discord servers you are
            authorized to manage.
          </li>
          <li>
            <strong className="font-medium text-fg-1">Audit records:</strong> Dashboard changes may be logged with
            who performed the action and when, for operational accountability.
          </li>
        </ul>
      </section>
      <section>
        <h2 className="text-section text-fg-1">Retention and contact</h2>
        <p>
          Retention periods depend on server configuration and operational backups. For access or deletion questions,
          contact the CLS owner. Discord&apos;s own privacy policy applies to your Discord account.
        </p>
      </section>
    </LegalPageShell>
  );
}
