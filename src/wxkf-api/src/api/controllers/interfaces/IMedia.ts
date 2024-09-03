export default interface IMedia {
    type: 'image' | 'voice' | 'video' | 'file',
    promise: Promise<{
        contentType: string;
        data: Buffer;
    }>
}