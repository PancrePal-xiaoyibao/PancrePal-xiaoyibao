export default interface IMessage {
    /** 消息发送者角色 */
    send_role: 'user' | 'assistant';
    /** 消息类型 */
    msgtype: 'text' | 'image' | 'voice' | 'video' | 'file' | 'location' | 'miniprogram' | 'channels_shop_product' | 'channels_shop_order' | 'merged_msg' | 'channels' | 'event';
    /** 消息ID */
    msgid: string;
    /** 客服账号ID */
    open_kfid: string;
    /** 客户UserID */
    external_userid: string;
    /** 消息发送时间 */
    send_time: number;
    /** 消息来源，3：客户回复的消息 4：系统推送的消息 */
    origin: number;
    /** 文本消息 */
    text?: {
        /** 文本内容 */
        content: string,
        /** 客户点击菜单消息，触发的回复消息中附带的菜单ID */
        menu_id?: string
    };
    /** 图片消息 */
    image?: {
        /** 图片文件id */
        media_id: string;
    };
    /** 语音消息 */
    voice?: {
        /** 语音文件ID */
        media_id: string;
    };
    /** 视频消息 */
    video?: {
        /** 视频文件ID */
        media_id: string;
    };
    /** 文件消息 */
    file?: {
        /** 文件ID */
        media_id: string;
    };
    /** 位置消息 */
    location?: {
        /** 位置名 */
        name: string;
        /** 地址详情说明 */
        address: string;
        /** 纬度 */
        latitude: number;
        /** 经度 */
        longitude: number;
    };
    /** 小程序消息 */
    miniprogram?: {
        /** 标题 */
        title: string;
        /** 小程序appid */
        appid: string;
        /** 点击消息卡片后进入的小程序页面路径 */
        pagepath: string;
        /** 小程序消息封面的文件ID */
        thumb_media_id: string;
    };
    /** 视频号商品消息 */
    channels_shop_product?: {
        /** 商品标题 */
        title: string;
        /** 商品ID */
        product_id: string;
        /** 商品图片 */
        head_image: string;
        /** 商品价格，以分为单位 */
        sales_price: string;
        /** 店铺名称 */
        shop_nickname: string;
        /** 店铺头像 */
        shop_head_image: string;
    };
    /** 视频号订单消息 */
    channels_shop_order?: {
        /** 订单号 */
        order_id: string;
        /** 商品标题 */
        product_titles: string;
        /** 订单价格描述 */
        price_wording: string;
        /** 订单状态 */
        state: string;
        /** 订单缩略图 */
        image_url: string;
        /** 店铺名称 */
        shop_nickname: string;
    };
    /** 聊天记录消息 */
    merged_msg?: {
        /** 聊天记录标题 */
        title: string;
        /** 消息记录内的消息内容 */
        item: {
            /** 消息类型 */
            msgtype: string;
            /** 发送时间 */
            send_time: number;
            /** 发送者名称 */
            sender_name: string;
            /** 消息内容，Json字符串，结构可参考本文档消息类型说明 */
            msg_content: string;
        }[]
    },
    /** 视频号消息 */
    channels?: {
        /** 视频号消息类型，1：视频号动态 2：视频号直播 3：视频号名片 */
        sub_type: number;
        /** 视频号名称 */
        nickname: string;
        /** 视频号动态标题，视频号消息类型为“1视频号动态”时，返回动态标题 */
        title: string;
    },
    /** 事件消息 */
    event?: {
        /** 事件类型，此处固定为：enter_session */
        event_type: string;
        /** 客服账号ID */
        open_kfid: string;
        /** 客户UserID */
        external_userid: string;
        /** 进入会话的场景值，获取客服账号链接开发者自定义的场景值 */
        scene: string;
        /** 进入会话的自定义参数，获取客服账号链接返回的url，开发者按规范拼接的scene_param参数 */
        scene_param: string;
        /** 如果满足发送欢迎语条件（条件为：用户在过去48小时里未收过欢迎语，且未向客服发过消息），会返回该字段。
可用该welcome_code调用发送事件响应消息接口给客户发送欢迎语。 */
        welcome_code: string;
        /** 进入会话的视频号信息，从视频号进入会话才有值 */
        wechat_channels: {
            /** 视频号名称，视频号场景值为1、2、3时返回此项 */
            nickname: string;
            /** 视频号小店名称，视频号场景值为4、5时返回此项 */
            shop_nickname: string;
            /** 视频号场景值，1：视频号主页，2：视频号直播间商品列表页，3：视频号商品橱窗页，4：视频号小店商品详情页，5：视频号小店订单页 */
            scene: number;
        };
    };
}