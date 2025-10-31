package xiaozhi.common.service.impl;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

import org.apache.ibatis.binding.MapperMethod;
import org.apache.ibatis.logging.Log;
import org.apache.ibatis.logging.LogFactory;
import org.apache.ibatis.session.SqlSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.enums.SqlMethod;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.metadata.OrderItem;
import com.baomidou.mybatisplus.core.toolkit.CollectionUtils;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import com.baomidou.mybatisplus.core.toolkit.ReflectionKit;
import com.baomidou.mybatisplus.core.toolkit.StringUtils;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.toolkit.SqlHelper;

import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.common.utils.ConvertUtils;

/**
 * 基础服务类，所有Service都要继承
 * Copyright (c) 人人开源 All rights reserved.
 * Website: https://www.renren.io
 */
public abstract class BaseServiceImpl<M extends BaseMapper<T>, T> implements BaseService<T> {
    @Autowired
    protected M baseDao;
    protected Log log = LogFactory.getLog(getClass());

    /**
     * 获取分页对象
     *
     * @param params            分页查询参数
     * @param defaultOrderField 默认排序字段
     * @param isAsc             排序方式
     * @see xiaozhi.common.constant.Constant
     *      params.put(Constant.PAGE, "1");
     *      params.put(Constant.LIMIT, "10");
     *      params.put(Constant.ORDER_FIELD, "field"); // 单个字段
     *      params.put(Constant.ORDER_FIELD, List.of("field1", "field2")); // 多个字段
     *      params.put(Constant.ORDER, "asc");
     */
    protected IPage<T> getPage(Map<String, Object> params, String defaultOrderField, boolean isAsc) {
        // 分页参数
        long curPage = 1;
        long limit = 10;

        if (params.get(Constant.PAGE) != null) {
            curPage = Long.parseLong((String) params.get(Constant.PAGE));
        }
        if (params.get(Constant.LIMIT) != null) {
            limit = Long.parseLong((String) params.get(Constant.LIMIT));
        }

        // 分页对象
        Page<T> page = new Page<>(curPage, limit);

        // 分页参数
        params.put(Constant.PAGE, page);

        // 排序字段
        Object orderField = params.get(Constant.ORDER_FIELD);
        String order = (String) params.get(Constant.ORDER);

        List<String> orderFields = new ArrayList<>();

        // 处理排序字段
        if (orderField instanceof String) {
            orderFields.add((String) orderField);
        } else if (orderField instanceof List) {
            orderFields.addAll((List<String>) orderField);
        }

        // 有排序字段则排序
        if (CollectionUtils.isNotEmpty(orderFields)) {
            if (StringUtils.isNotBlank(order) && Constant.ASC.equalsIgnoreCase(order)) {
                return page.addOrder(OrderItem.ascs(orderFields.toArray(new String[0])));
            } else {
                return page.addOrder(OrderItem.descs(orderFields.toArray(new String[0])));
            }
        }

        // 没有排序字段，使用默认排序
        if (StringUtils.isNotBlank(defaultOrderField)) {
            if (isAsc) {
                page.addOrder(OrderItem.asc(defaultOrderField));
            } else {
                page.addOrder(OrderItem.desc(defaultOrderField));
            }
        }

        return page;
    }

    protected <D> PageData<D> getPageData(List<?> list, long total, Class<D> target) {
        List<D> targetList = ConvertUtils.sourceToTarget(list, target);

        return new PageData<>(targetList, total);
    }

    protected <D> PageData<D> getPageData(IPage<?> page, Class<D> target) {
        return getPageData(page.getRecords(), page.getTotal(), target);
    }

    protected void paramsToLike(Map<String, Object> params, String... likes) {
        for (String like : likes) {
            String val = (String) params.get(like);
            if (StringUtils.isNotBlank(val)) {
                params.put(like, "%" + val + "%");
            } else {
                params.put(like, null);
            }
        }
    }

    /**
     * <p>
     * 判断数据库操作是否成功
     * </p>
     * <p>
     * 注意！！ 该方法为 Integer 判断，不可传入 int 基本类型
     * </p>
     *
     * @param result 数据库操作返回影响条数
     * @return boolean
     */
    protected static boolean retBool(Integer result) {
        return SqlHelper.retBool(result);
    }

    protected Class<M> currentMapperClass() {
        return (Class<M>) ReflectionKit.getSuperClassGenericType(this.getClass(), BaseServiceImpl.class, 0);
    }

    @Override
    public Class<T> currentModelClass() {
        return (Class<T>) ReflectionKit.getSuperClassGenericType(this.getClass(), BaseServiceImpl.class, 1);
    }

    protected String getSqlStatement(SqlMethod sqlMethod) {
        return SqlHelper.getSqlStatement(this.currentMapperClass(), sqlMethod);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insert(T entity) {
        return BaseServiceImpl.retBool(baseDao.insert(entity));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<T> entityList) {
        return insertBatch(entityList, 100);
    }

    /**
     * 批量插入
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean insertBatch(Collection<T> entityList, int batchSize) {
        String sqlStatement = getSqlStatement(SqlMethod.INSERT_ONE);
        return executeBatch(entityList, batchSize, (sqlSession, entity) -> sqlSession.insert(sqlStatement, entity));
    }

    /**
     * 执行批量操作
     */
    @SuppressWarnings("deprecation")
    protected <E> boolean executeBatch(Collection<E> list, int batchSize, BiConsumer<SqlSession, E> consumer) {
        return SqlHelper.executeBatch(this.currentModelClass(), this.log, list, batchSize, consumer);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(T entity) {
        return BaseServiceImpl.retBool(baseDao.updateById(entity));
    }

    @Override
    public boolean update(T entity, Wrapper<T> updateWrapper) {
        return BaseServiceImpl.retBool(baseDao.update(entity, updateWrapper));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<T> entityList) {
        return updateBatchById(entityList, 30);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateBatchById(Collection<T> entityList, int batchSize) {
        String sqlStatement = getSqlStatement(SqlMethod.UPDATE_BY_ID);
        return executeBatch(entityList, batchSize, (sqlSession, entity) -> {
            MapperMethod.ParamMap<T> param = new MapperMethod.ParamMap<>();
            param.put(Constants.ENTITY, entity);
            sqlSession.update(sqlStatement, param);
        });
    }

    @Override
    public T selectById(Serializable id) {
        return baseDao.selectById(id);
    }

    @Override
    public boolean deleteById(Serializable id) {
        return SqlHelper.retBool(baseDao.deleteById(id));
    }

    @Override
    public boolean deleteBatchIds(Collection<? extends Serializable> idList) {
        return SqlHelper.retBool(baseDao.deleteBatchIds(idList));
    }
}