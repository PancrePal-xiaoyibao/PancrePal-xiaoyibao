import { log } from './utils/logger.js';
import { otaStatusStyle } from './document.js'

// WebSocket 连接
export async function webSocketConnect(otaUrl,wsUrl,config){
    if (!validateWsUrl(wsUrl)) {
        return;          // 直接返回，不再往下执行
    }

    if (!validateConfig(config)) {
        return;
    }
    const ok = await sendOTA(otaUrl, config);
    if (!ok) return;

    // 使用自定义WebSocket实现以添加认证头信息
    let connUrl = new URL(wsUrl);
    // 添加认证参数
    connUrl.searchParams.append('device-id', config.deviceId);
    connUrl.searchParams.append('client-id', config.clientId);
    log(`正在连接: ${connUrl.toString()}`, 'info');

    return new WebSocket(connUrl.toString());
}

// 验证配置
function validateConfig(config) {
    if (!config.deviceMac) {
        log('设备MAC地址不能为空', 'error');
        return false;
    }
    if (!config.clientId) {
        log('客户端ID不能为空', 'error');
        return false;
    }
    return true;
}

// 判断wsUrl路径是否存在错误
function validateWsUrl(wsUrl){
    if (wsUrl === '') return false;
    // 检查URL格式
    if (!wsUrl.startsWith('ws://') && !wsUrl.startsWith('wss://')) {
        log('URL格式错误，必须以ws://或wss://开头', 'error');
        return false;
    }
    return true
}


// OTA发送请求，验证状态
async function sendOTA(otaUrl, config) {
    try {
        const res = await fetch(otaUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Device-Id': config.deviceId,
                'Client-Id': config.clientId
            },
            body: JSON.stringify({
                version: 0,
                uuid: '',
                application: {
                    name: 'xiaozhi-web-test',
                    version: '1.0.0',
                    compile_time: '2025-04-16 10:00:00',
                    idf_version: '4.4.3',
                    elf_sha256: '1234567890abcdef1234567890abcdef1234567890abcdef'
                },
                ota: { label: 'xiaozhi-web-test' },
                board: {
                    type: 'xiaozhi-web-test',
                    ssid: 'xiaozhi-web-test',
                    rssi: 0,
                    channel: 0,
                    ip: '192.168.1.1',
                    mac: config.deviceMac
                },
                flash_size: 0,
                minimum_free_heap_size: 0,
                mac_address: config.deviceMac,
                chip_model_name: '',
                chip_info: { model: 0, cores: 0, revision: 0, features: 0 },
                partition_table: [{ label: '', type: 0, subtype: 0, address: 0, size: 0 }]
            })
        });

        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);

        const result = await res.json();
        otaStatusStyle(true)
        return true; // 成功
    } catch (err) {
        otaStatusStyle(false)
        return false; // 失败
    }
}





