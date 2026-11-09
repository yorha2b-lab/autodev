module.exports = ({ columns, fileName }) => `根据columns的dataIndex字段生成一个简单的接口mock数据: ${JSON.stringify(columns)},格式为{POST /api/${fileName}:{data:2条真实mock数据]}}`
