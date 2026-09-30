import DiscordProvider from "next-auth/providers/discord";
import { AuthOptions } from "next-auth";
import { createDashboardSession, revokeDashboardSession } from "@/lib/botInternal";

export const authOptions: AuthOptions = {
  providers: [
    DiscordProvider({
      clientId: process.env.DISCORD_CLIENT_ID || "",
      clientSecret: process.env.DISCORD_CLIENT_SECRET || "",
      authorization: { params: { scope: "identify" } },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account?.access_token) {
        const created = await createDashboardSession(account.access_token);
        token.dashboardSessionId = created.sessionId;
        token.sub = created.discordUserId;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user && token.sub) {
        session.user.id = token.sub;
      }
      const extended = session as typeof session & { dashboardSessionId?: string };
      extended.dashboardSessionId = token.dashboardSessionId as string | undefined;
      return extended;
    },
  },
  events: {
    async signOut(message) {
      const token = "token" in message ? message.token : null;
      const sid = token?.dashboardSessionId as string | undefined;
      if (sid) {
        await revokeDashboardSession(sid);
      }
    },
  },
  pages: {
    signIn: "/",
  },
};
