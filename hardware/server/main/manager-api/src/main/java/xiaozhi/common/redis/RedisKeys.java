package xiaozhi.common.redis;

/**
 * Redis Key 常量类
 * Copyright (c) 人人开源 All rights reserved.
 * Website: https://www.renren.io
 */
public class RedisKeys {
    /**
     * 系统参数Key
     */
    public static String getSysParamsKey() {
        return "sys:params";
    }

    /**
     * 验证码Key
     */
    public static String getCaptchaKey(String uuid) {
        return "sys:captcha:" + uuid;
    }

    /**
     * 未注册设备验证码Key
     */
    public static String getDeviceCaptchaKey(String captcha) {
        return "sys:device:captcha:" + captcha;
    }

    /**
     * 用户id的Key
     */
    public static String getUserIdKey(Long userid) {
        return "sys:username:id:" + userid;
    }

    /**
     * 模型名称的Key
     */
    public static String getModelNameById(String id) {
        return "model:name:" + id;
    }

    /**
     * 模型配置的Key
     */
    public static String getModelConfigById(String id) {
        return "model:data:" + id;
    }

    /**
     * 获取音色名称缓存key
     */
    public static String getTimbreNameById(String id) {
        return "timbre:name:" + id;
    }

    /**
     * 获取设备数量缓存key
     */
    public static String getAgentDeviceCountById(String id) {
        return "agent:device:count:" + id;
    }

    /**
     * 获取智能体最后连接时间缓存key
     */
    public static String getAgentDeviceLastConnectedAtById(String id) {
        return "agent:device:lastConnected:" + id;
    }

    /**
     * 获取系统配置缓存key
     */
    public static String getServerConfigKey() {
        return "server:config";
    }

    /**
     * 获取音色详情缓存key
     */
    public static String getTimbreDetailsKey(String id) {
        return "timbre:details:" + id;
    }

    /**
     * 获取版本号Key
     */
    public static String getVersionKey() {
        return "sys:version";
    }

    /**
     * OTA固件ID的Key
     */
    public static String getOtaIdKey(String uuid) {
        return "ota:id:" + uuid;
    }

    /**
     * OTA固件下载次数的Key
     */
    public static String getOtaDownloadCountKey(String uuid) {
        return "ota:download:count:" + uuid;
    }

    /**
     * 获取字典数据的缓存key
     */
    public static String getDictDataByTypeKey(String dictType) {
        return "sys:dict:data:" + dictType;
    }

    /**
     * 获取智能体音频ID的缓存key
     */
    public static String getAgentAudioIdKey(String uuid) {
        return "agent:audio:id:" + uuid;
    }

    /**
     * 获取短信验证码的缓存key
     */
    public static String getSMSValidateCodeKey(String phone) {
        return "sms:Validate:Code:" + phone;
    }

    /**
     * 获取短信验证码最后发送时间的缓存key
     */
    public static String getSMSLastSendTimeKey(String phone) {
        return "sms:Validate:Code:" + phone + ":last_send_time";
    }

    /**
     * 获取短信验证码今日发送次数的缓存key
     */
    public static String getSMSTodayCountKey(String phone) {
        return "sms:Validate:Code:" + phone + ":today_count";
    }

}
