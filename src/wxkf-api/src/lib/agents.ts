import yaml from 'yaml';
import _ from 'lodash';
import fs from 'fs-extra';
import logger from './logger.ts';
import IAgentConfig from './interfaces/IAgentConfig.ts';

let agents: IAgentConfig[] = [];

if(!fs.existsSync('agents.yml'))
    logger.warn('agents.yml未找到, 请重命名项目根目录下的agents.yml.template为agents.yml并填写配置');
else
    agents = yaml.parse(fs.readFileSync('agents.yml').toString()) || [];

export default agents;