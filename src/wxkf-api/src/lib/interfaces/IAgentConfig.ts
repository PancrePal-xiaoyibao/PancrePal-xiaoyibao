export default interface IAgentConfig {
    id: string;
    name: string;
    welcome?: string;
    api: string;
    apiKey: string;
    avatarUrl: string;
    maxRounds: number;
    enabled: boolean;
    openKfId?: string;
    contactUrl?: string;
}