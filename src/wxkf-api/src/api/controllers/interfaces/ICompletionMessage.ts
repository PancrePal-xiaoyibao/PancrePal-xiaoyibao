export default interface ICompletionMessage {
    role: 'system' | 'user' | 'assistant',
    content: string | Record<string, any>[]
}