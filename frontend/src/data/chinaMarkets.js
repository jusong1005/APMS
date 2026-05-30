const provinceCityGroups = [
  { label: '北京市', cities: ['北京市'] },
  { label: '天津市', cities: ['天津市'] },
  { label: '河北省', cities: ['石家庄市', '唐山市', '秦皇岛市', '邯郸市', '邢台市', '保定市', '张家口市', '承德市', '沧州市', '廊坊市', '衡水市'] },
  { label: '山西省', cities: ['太原市', '大同市', '阳泉市', '长治市', '晋城市', '朔州市', '晋中市', '运城市', '忻州市', '临汾市', '吕梁市'] },
  { label: '内蒙古自治区', cities: ['呼和浩特市', '包头市', '乌海市', '赤峰市', '通辽市', '鄂尔多斯市', '呼伦贝尔市', '巴彦淖尔市', '乌兰察布市', '兴安盟', '锡林郭勒盟', '阿拉善盟'] },
  { label: '辽宁省', cities: ['沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市', '丹东市', '锦州市', '营口市', '阜新市', '辽阳市', '盘锦市', '铁岭市', '朝阳市', '葫芦岛市'] },
  { label: '吉林省', cities: ['长春市', '吉林市', '四平市', '辽源市', '通化市', '白山市', '松原市', '白城市', '延边朝鲜族自治州'] },
  { label: '黑龙江省', cities: ['哈尔滨市', '齐齐哈尔市', '鸡西市', '鹤岗市', '双鸭山市', '大庆市', '伊春市', '佳木斯市', '七台河市', '牡丹江市', '黑河市', '绥化市', '大兴安岭地区'] },
  { label: '上海市', cities: ['上海市'] },
  { label: '江苏省', cities: ['南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市'] },
  { label: '浙江省', cities: ['杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市'] },
  { label: '安徽省', cities: ['合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市', '淮北市', '铜陵市', '安庆市', '黄山市', '滁州市', '阜阳市', '宿州市', '六安市', '亳州市', '池州市', '宣城市'] },
  { label: '福建省', cities: ['福州市', '厦门市', '莆田市', '三明市', '泉州市', '漳州市', '南平市', '龙岩市', '宁德市'] },
  { label: '江西省', cities: ['南昌市', '景德镇市', '萍乡市', '九江市', '新余市', '鹰潭市', '赣州市', '吉安市', '宜春市', '抚州市', '上饶市'] },
  { label: '山东省', cities: ['济南市', '青岛市', '淄博市', '枣庄市', '东营市', '烟台市', '潍坊市', '济宁市', '泰安市', '威海市', '日照市', '临沂市', '德州市', '聊城市', '滨州市', '菏泽市', '寿光市'] },
  { label: '河南省', cities: ['郑州市', '开封市', '洛阳市', '平顶山市', '安阳市', '鹤壁市', '新乡市', '焦作市', '濮阳市', '许昌市', '漯河市', '三门峡市', '南阳市', '商丘市', '信阳市', '周口市', '驻马店市', '济源市'] },
  { label: '湖北省', cities: ['武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '鄂州市', '荆门市', '孝感市', '荆州市', '黄冈市', '咸宁市', '随州市', '恩施土家族苗族自治州'] },
  { label: '湖南省', cities: ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界市', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西土家族苗族自治州'] },
  { label: '广东省', cities: ['广州市', '韶关市', '深圳市', '珠海市', '汕头市', '佛山市', '江门市', '湛江市', '茂名市', '肇庆市', '惠州市', '梅州市', '汕尾市', '河源市', '阳江市', '清远市', '东莞市', '中山市', '潮州市', '揭阳市', '云浮市'] },
  { label: '广西壮族自治区', cities: ['南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港市', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市'] },
  { label: '海南省', cities: ['海口市', '三亚市', '三沙市', '儋州市'] },
  { label: '重庆市', cities: ['重庆市'] },
  { label: '四川省', cities: ['成都市', '自贡市', '攀枝花市', '泸州市', '德阳市', '绵阳市', '广元市', '遂宁市', '内江市', '乐山市', '南充市', '眉山市', '宜宾市', '广安市', '达州市', '雅安市', '巴中市', '资阳市', '阿坝藏族羌族自治州', '甘孜藏族自治州', '凉山彝族自治州'] },
  { label: '贵州省', cities: ['贵阳市', '六盘水市', '遵义市', '安顺市', '毕节市', '铜仁市', '黔西南布依族苗族自治州', '黔东南苗族侗族自治州', '黔南布依族苗族自治州'] },
  { label: '云南省', cities: ['昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市', '楚雄彝族自治州', '红河哈尼族彝族自治州', '文山壮族苗族自治州', '西双版纳傣族自治州', '大理白族自治州', '德宏傣族景颇族自治州', '怒江傈僳族自治州', '迪庆藏族自治州'] },
  { label: '陕西省', cities: ['西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市'] },
]

const featuredMarkets = new Map([
  ['北京市|北京市', [{ value: 'beijing-xinfadi', label: '北京新发地批发市场', offset: 0.32 }, { value: 'beijing-dayanglu', label: '北京大洋路批发市场', offset: 0.24 }]],
  ['上海市|上海市', [{ label: '上海江桥批发市场', offset: 0.18 }, { label: '上海西郊国际农产品交易中心', offset: 0.22 }]],
  ['重庆市|重庆市', [{ label: '重庆双福国际农贸城', offset: 0.12 }]],
  ['江苏省|南京市', [{ label: '南京众彩农副产品物流中心', offset: 0.08 }]],
  ['浙江省|杭州市', [{ label: '杭州农副产品物流中心', offset: 0.11 }]],
  ['山东省|济南市', [{ value: 'jinan-qilibao', label: '济南七里堡批发市场', offset: -0.02 }, { value: 'jinan-kuangshan', label: '济南匡山农产品市场', offset: 0.03 }]],
  ['山东省|寿光市', [{ value: 'shouguang-logistics', label: '寿光农产品物流园', offset: 0.1 }, { value: 'shouguang-vegetable', label: '寿光蔬菜批发市场', offset: 0.04 }]],
  ['河南省|郑州市', [{ value: 'zhengzhou-wanbang', label: '郑州万邦国际农产品物流城', offset: -0.06 }, { value: 'zhengzhou-chenzhai', label: '陈寨蔬菜批发市场', offset: -0.1 }]],
  ['湖北省|武汉市', [{ label: '武汉白沙洲农副产品大市场', offset: 0.06 }]],
  ['湖南省|长沙市', [{ label: '长沙红星农副产品大市场', offset: 0.07 }]],
  ['广东省|广州市', [{ label: '广州江南果菜批发市场', offset: 0.2 }]],
  ['广东省|深圳市', [{ label: '深圳海吉星国际农产品物流园', offset: 0.26 }]],
  ['四川省|成都市', [{ value: 'chengdu-baijia', label: '成都白家农产品市场', offset: 0.14 }, { value: 'chengdu-mengyang', label: '濛阳农副产品综合批发市场', offset: 0.19 }]]
])

export const marketTree = provinceCityGroups.map((province, provinceIndex) => ({
  value: `province-${provinceIndex}`,
  label: province.label,
  children: province.cities.map((city, cityIndex) => ({
    value: `province-${provinceIndex}-city-${cityIndex}`,
    label: city,
    children: marketsForCity(province.label, city, provinceIndex, cityIndex)
  }))
}))

export const cityCoverageStats = {
  provinces: provinceCityGroups.length,
  cities: provinceCityGroups.reduce((sum, province) => sum + province.cities.length, 0),
  markets: marketTree.reduce((sum, province) => sum + province.children.reduce((citySum, city) => citySum + city.children.length, 0), 0)
}

export const defaultAreaPaths = [
  findMarketPath('山东省', '寿光市', '寿光农产品物流园'),
  findMarketPath('山东省', '济南市', '济南七里堡批发市场'),
  findMarketPath('河南省', '郑州市', '郑州万邦国际农产品物流城'),
  findMarketPath('北京市', '北京市', '北京新发地批发市场')
]

function marketsForCity(province, city, provinceIndex, cityIndex) {
  const featured = featuredMarkets.get(`${province}|${city}`)
  const markets = featured?.length ? featured : [{ label: `${trimCitySuffix(city)}农产品批发市场` }]

  return markets.map((market, marketIndex) => ({
    value: market.value ?? `province-${provinceIndex}-city-${cityIndex}-market-${marketIndex}`,
    label: market.label,
    offset: market.offset ?? createMarketOffset(`${province}${city}${market.label}`)
  }))
}

function findMarketPath(provinceLabel, cityLabel, marketLabel) {
  const province = marketTree.find((item) => item.label === provinceLabel)
  const city = province?.children.find((item) => item.label === cityLabel)
  const market = city?.children.find((item) => item.label === marketLabel)
  return province && city && market ? [province.value, city.value, market.value] : []
}

function trimCitySuffix(city) {
  return city.replace(/(特别行政区|自治州|自治盟|地区|市|县|盟)$/u, '')
}

function createMarketOffset(text) {
  const hash = Array.from(text).reduce((sum, character) => sum + character.charCodeAt(0), 0)
  return Math.round((((hash % 61) - 30) / 200) * 100) / 100
}