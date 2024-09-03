import yaml from 'yaml';
import fs from 'fs-extra';
import logger from './logger.ts';

if(!fs.existsSync('secret.yml')) {
    logger.warn('secret.yml未找到, 请重命名项目根目录下的secret.yml.template为secret.yml并填写配置');
    process.exit(0);
}

const secret: {
    /** 企业ID */
    WXKF_API_CORP_ID: string;
    /** Secret */
    WXKF_API_CORP_SECRET: string;
    /** Token */
    WXKF_API_TOKEN: string;
    /** EncodingAESKey */
    WXKF_API_ENCODING_AES_KEY: string;
} = yaml.parse(fs.readFileSync('secret.yml').toString());

export default secret;