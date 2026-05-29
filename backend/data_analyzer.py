"""
数据分析模块 - 多维度统计分析与图表生成

实现农产品价格数据的多维度统计分析，包括：
- 价格趋势分析（折线图）
- 月度价格分析（柱状图）
- 地区差异分析（对比图）
- 气象影响分析（相关性热力图）
- 价格波动分析（波动图）
- 统计分析报告生成（不少于500字）

每张图表包含标题、坐标轴标签和数据来源说明。
"""

import os
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # 非交互式后端，适合服务器环境
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

from models.schemas import AnalysisResult

# 尝试设置中文字体
plt.rcParams["axes.unicode_minus"] = False
for font_name in ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]:
    if any(font_name in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [font_name]
        break


class DataAnalyzer:
    """多维度统计分析模块

    对清洗后的农产品价格和气象数据进行统计分析，
    生成可视化图表并输出分析报告。
    """

    def __init__(self, output_dir: Optional[str] = None):
        """初始化数据分析器

        Args:
            output_dir: 图表输出目录路径，默认为项目根目录下的 output/charts/
        """
        if output_dir is None:
            project_root = Path(__file__).parent.parent.resolve()
            self.output_dir = project_root / "output" / "charts"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_price_trend(self, df: pd.DataFrame) -> AnalysisResult:
        """价格趋势分析，生成折线图

        按日期和农产品分组，展示各农产品价格随时间的变化趋势。

        Args:
            df: 包含 date、product_name、average_price 列的 DataFrame

        Returns:
            AnalysisResult: 包含图表数据和文件路径的分析结果
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # 按日期和产品分组计算均价
        trend_data = (
            df.groupby(["date", "product_name"])["average_price"]
            .mean()
            .reset_index()
        )

        # 生成折线图
        fig, ax = plt.subplots(figsize=(12, 6))
        for product in trend_data["product_name"].unique():
            product_data = trend_data[trend_data["product_name"] == product]
            ax.plot(
                product_data["date"],
                product_data["average_price"],
                label=product,
                linewidth=1.5,
            )

        ax.set_title("农产品价格趋势分析")
        ax.set_xlabel("日期")
        ax.set_ylabel("平均价格（元/公斤）")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()

        # 添加数据来源说明
        fig.text(
            0.5, 0.01,
            "数据来源：农产品批发市场价格信息系统",
            ha="center", fontsize=8, style="italic",
        )

        chart_path = str(self.output_dir / "price_trend.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # 构建分析描述
        products = trend_data["product_name"].unique().tolist()
        date_range = f"{trend_data['date'].min().strftime('%Y-%m-%d')} 至 {trend_data['date'].max().strftime('%Y-%m-%d')}"
        description = (
            f"价格趋势分析覆盖{len(products)}种农产品（{', '.join(products)}），"
            f"时间范围为{date_range}。"
        )

        return AnalysisResult(
            analysis_type="trend",
            title="农产品价格趋势分析",
            chart_data={
                "title": "农产品价格趋势分析",
                "xlabel": "日期",
                "ylabel": "平均价格（元/公斤）",
                "data_source": "农产品批发市场价格信息系统",
                "products": products,
                "date_range": date_range,
            },
            chart_path=chart_path,
            description=description,
        )

    def analyze_monthly_price(self, df: pd.DataFrame) -> AnalysisResult:
        """月度价格分析，生成柱状图

        按月份统计各农产品的平均价格，展示月度价格变化。

        Args:
            df: 包含 date、product_name、average_price 列的 DataFrame

        Returns:
            AnalysisResult: 包含图表数据和文件路径的分析结果
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.to_period("M").astype(str)

        # 按月份和产品分组计算均价
        monthly_data = (
            df.groupby(["month", "product_name"])["average_price"]
            .mean()
            .reset_index()
        )

        # 生成柱状图
        fig, ax = plt.subplots(figsize=(12, 6))
        products = monthly_data["product_name"].unique()
        months = sorted(monthly_data["month"].unique())
        x = np.arange(len(months))
        width = 0.8 / len(products)

        for i, product in enumerate(products):
            product_data = monthly_data[monthly_data["product_name"] == product]
            # 确保每个月都有数据，缺失的用0填充
            values = []
            for month in months:
                month_val = product_data[product_data["month"] == month]["average_price"]
                values.append(month_val.values[0] if len(month_val) > 0 else 0)
            offset = (i - len(products) / 2 + 0.5) * width
            ax.bar(x + offset, values, width, label=product)

        ax.set_title("月度农产品价格分析")
        ax.set_xlabel("月份")
        ax.set_ylabel("平均价格（元/公斤）")
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()

        fig.text(
            0.5, 0.01,
            "数据来源：农产品批发市场价格信息系统",
            ha="center", fontsize=8, style="italic",
        )

        chart_path = str(self.output_dir / "monthly_price.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        description = (
            f"月度价格分析涵盖{len(months)}个月份，"
            f"共{len(products)}种农产品的月均价格对比。"
        )

        return AnalysisResult(
            analysis_type="monthly",
            title="月度农产品价格分析",
            chart_data={
                "title": "月度农产品价格分析",
                "xlabel": "月份",
                "ylabel": "平均价格（元/公斤）",
                "data_source": "农产品批发市场价格信息系统",
                "months": months,
                "products": list(products),
            },
            chart_path=chart_path,
            description=description,
        )

    def analyze_regional_difference(self, df: pd.DataFrame) -> AnalysisResult:
        """地区差异分析，生成对比图

        按地区统计各农产品的平均价格，展示地区间价格差异。

        Args:
            df: 包含 region、product_name、average_price 列的 DataFrame

        Returns:
            AnalysisResult: 包含图表数据和文件路径的分析结果
        """
        df = df.copy()

        # 按地区和产品分组计算均价
        regional_data = (
            df.groupby(["region", "product_name"])["average_price"]
            .mean()
            .reset_index()
        )

        # 生成分组柱状图
        fig, ax = plt.subplots(figsize=(10, 6))
        regions = sorted(regional_data["region"].unique())
        products = regional_data["product_name"].unique()
        x = np.arange(len(regions))
        width = 0.8 / len(products)

        for i, product in enumerate(products):
            product_data = regional_data[regional_data["product_name"] == product]
            values = []
            for region in regions:
                region_val = product_data[product_data["region"] == region]["average_price"]
                values.append(region_val.values[0] if len(region_val) > 0 else 0)
            offset = (i - len(products) / 2 + 0.5) * width
            ax.bar(x + offset, values, width, label=product)

        ax.set_title("地区农产品价格差异对比")
        ax.set_xlabel("地区")
        ax.set_ylabel("平均价格（元/公斤）")
        ax.set_xticks(x)
        ax.set_xticklabels(regions)
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()

        fig.text(
            0.5, 0.01,
            "数据来源：农产品批发市场价格信息系统",
            ha="center", fontsize=8, style="italic",
        )

        chart_path = str(self.output_dir / "regional_difference.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # 计算地区间价格差异
        region_avg = df.groupby("region")["average_price"].mean()
        max_region = region_avg.idxmax()
        min_region = region_avg.idxmin()
        price_diff = region_avg.max() - region_avg.min()

        description = (
            f"地区差异分析覆盖{len(regions)}个地区（{', '.join(regions)}），"
            f"其中{max_region}地区平均价格最高，{min_region}地区平均价格最低，"
            f"地区间最大价格差异为{price_diff:.2f}元/公斤。"
        )

        return AnalysisResult(
            analysis_type="regional",
            title="地区农产品价格差异对比",
            chart_data={
                "title": "地区农产品价格差异对比",
                "xlabel": "地区",
                "ylabel": "平均价格（元/公斤）",
                "data_source": "农产品批发市场价格信息系统",
                "regions": regions,
                "products": list(products),
            },
            chart_path=chart_path,
            description=description,
        )

    def analyze_weather_correlation(self, df: pd.DataFrame) -> AnalysisResult:
        """气象影响分析，生成相关性热力图

        计算气象因素（气温、降雨量、湿度等）与价格之间的相关系数，
        生成相关性热力图。

        Args:
            df: 包含 average_price 和气象字段的 DataFrame

        Returns:
            AnalysisResult: 包含图表数据和文件路径的分析结果
        """
        df = df.copy()

        # 选择气象和价格相关的数值列
        weather_cols = [
            "average_temperature",
            "highest_temperature",
            "lowest_temperature",
            "rainfall",
            "humidity",
            "sunshine_duration",
        ]
        price_cols = ["average_price", "highest_price", "lowest_price"]

        # 筛选存在的列
        available_weather = [c for c in weather_cols if c in df.columns]
        available_price = [c for c in price_cols if c in df.columns]
        analysis_cols = available_price + available_weather

        # 计算相关系数矩阵
        corr_matrix = df[analysis_cols].corr()

        # 生成热力图
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr_matrix.values, cmap="RdYlBu_r", aspect="auto",
                       vmin=-1, vmax=1)

        # 设置标签
        col_labels = [self._translate_column(c) for c in corr_matrix.columns]
        ax.set_xticks(np.arange(len(col_labels)))
        ax.set_yticks(np.arange(len(col_labels)))
        ax.set_xticklabels(col_labels, rotation=45, ha="right")
        ax.set_yticklabels(col_labels)

        # 在每个格子中显示相关系数值
        for i in range(len(col_labels)):
            for j in range(len(col_labels)):
                value = corr_matrix.values[i, j]
                color = "white" if abs(value) > 0.5 else "black"
                ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                        color=color, fontsize=8)

        ax.set_title("气象因素与价格相关性热力图")
        ax.set_xlabel("变量")
        ax.set_ylabel("变量")
        fig.colorbar(im, ax=ax, label="相关系数")
        fig.tight_layout()

        fig.text(
            0.5, 0.01,
            "数据来源：农产品批发市场价格信息系统与气象观测数据",
            ha="center", fontsize=8, style="italic",
        )

        chart_path = str(self.output_dir / "weather_correlation.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # 找出与价格相关性最强的气象因素
        if available_weather and "average_price" in corr_matrix.columns:
            price_corr = corr_matrix.loc["average_price", available_weather]
            # 过滤掉NaN值（当某列方差为0时相关系数为NaN）
            valid_corr = price_corr.dropna()
            if len(valid_corr) > 0:
                max_corr_factor = valid_corr.abs().idxmax()
                max_corr_value = valid_corr[max_corr_factor]
                corr_desc = (
                    f"与平均价格相关性最强的气象因素为"
                    f"{self._translate_column(max_corr_factor)}，"
                    f"相关系数为{max_corr_value:.3f}。"
                )
            else:
                corr_desc = "气象因素与价格之间的相关性无法计算（数据方差不足）。"
        else:
            corr_desc = "气象因素与价格之间存在一定相关性。"

        description = f"气象影响分析计算了{len(available_weather)}个气象因素与价格的相关性。{corr_desc}"

        return AnalysisResult(
            analysis_type="weather",
            title="气象因素与价格相关性热力图",
            chart_data={
                "title": "气象因素与价格相关性热力图",
                "xlabel": "变量",
                "ylabel": "变量",
                "data_source": "农产品批发市场价格信息系统与气象观测数据",
                "correlation_matrix": corr_matrix.to_dict(),
            },
            chart_path=chart_path,
            description=description,
        )

    def analyze_price_volatility(self, df: pd.DataFrame) -> AnalysisResult:
        """价格波动分析，生成波动图

        计算各农产品价格的标准差和变异系数，展示价格波动情况。

        Args:
            df: 包含 date、product_name、average_price 列的 DataFrame

        Returns:
            AnalysisResult: 包含图表数据和文件路径的分析结果
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # 按周计算价格波动（标准差）
        df["week"] = df["date"].dt.isocalendar().week.astype(int)
        df["year_week"] = df["date"].dt.strftime("%Y-W%U")

        weekly_volatility = (
            df.groupby(["year_week", "product_name"])["average_price"]
            .std()
            .reset_index()
            .rename(columns={"average_price": "price_std"})
        )
        # 填充NaN（单条记录的周标准差为NaN）
        weekly_volatility["price_std"] = weekly_volatility["price_std"].fillna(0)

        # 生成波动图
        fig, ax = plt.subplots(figsize=(12, 6))
        products = weekly_volatility["product_name"].unique()
        weeks = sorted(weekly_volatility["year_week"].unique())

        for product in products:
            product_data = weekly_volatility[weekly_volatility["product_name"] == product]
            product_data = product_data.sort_values("year_week")
            ax.plot(
                range(len(product_data)),
                product_data["price_std"].values,
                label=product,
                linewidth=1.5,
                marker="o",
                markersize=3,
            )

        ax.set_title("农产品价格波动分析（周标准差）")
        ax.set_xlabel("时间（周）")
        ax.set_ylabel("价格标准差（元/公斤）")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)

        # 简化x轴标签
        tick_step = max(1, len(weeks) // 8)
        ax.set_xticks(range(0, len(weeks), tick_step))
        ax.set_xticklabels(
            [weeks[i] for i in range(0, len(weeks), tick_step)],
            rotation=45, ha="right",
        )
        fig.tight_layout()

        fig.text(
            0.5, 0.01,
            "数据来源：农产品批发市场价格信息系统",
            ha="center", fontsize=8, style="italic",
        )

        chart_path = str(self.output_dir / "price_volatility.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # 计算整体波动统计
        overall_volatility = df.groupby("product_name")["average_price"].agg(
            ["mean", "std"]
        )
        overall_volatility["cv"] = (
            overall_volatility["std"] / overall_volatility["mean"] * 100
        )
        most_volatile = overall_volatility["cv"].idxmax()
        least_volatile = overall_volatility["cv"].idxmin()

        description = (
            f"价格波动分析显示，{most_volatile}的价格波动最大"
            f"（变异系数{overall_volatility.loc[most_volatile, 'cv']:.1f}%），"
            f"{least_volatile}的价格最为稳定"
            f"（变异系数{overall_volatility.loc[least_volatile, 'cv']:.1f}%）。"
        )

        return AnalysisResult(
            analysis_type="volatility",
            title="农产品价格波动分析",
            chart_data={
                "title": "农产品价格波动分析（周标准差）",
                "xlabel": "时间（周）",
                "ylabel": "价格标准差（元/公斤）",
                "data_source": "农产品批发市场价格信息系统",
                "products": list(products),
            },
            chart_path=chart_path,
            description=description,
        )

    def generate_report(self, results: List[AnalysisResult]) -> str:
        """生成统计分析报告

        基于各项分析结果，生成不少于500字的综合统计分析报告。

        Args:
            results: 各项分析的 AnalysisResult 列表

        Returns:
            str: 统计分析报告文本（不少于500字符）
        """
        report_sections = []

        # 报告标题
        report_sections.append("=" * 60)
        report_sections.append("农产品价格数据统计分析报告")
        report_sections.append("=" * 60)
        report_sections.append("")

        # 报告概述
        report_sections.append("一、分析概述")
        report_sections.append("-" * 40)
        report_sections.append(
            "本报告基于农产品批发市场价格信息系统和气象观测数据，"
            "对农产品价格进行多维度统计分析。分析内容涵盖价格趋势变化、"
            "月度价格对比、地区差异比较、气象因素影响以及价格波动特征等方面，"
            "旨在揭示农产品价格的变化规律和主要影响因素，为市场决策提供数据支撑。"
        )
        report_sections.append("")

        # 各分析结果详述
        section_titles = {
            "trend": "二、价格趋势分析",
            "monthly": "三、月度价格分析",
            "regional": "四、地区差异分析",
            "weather": "五、气象影响分析",
            "volatility": "六、价格波动分析",
        }

        section_details = {
            "trend": (
                "通过对各农产品价格的时间序列分析，可以观察到价格随季节和市场供需变化"
                "呈现出明显的波动趋势。折线图直观展示了不同农产品在分析期间内的价格走势，"
                "有助于识别价格的周期性变化和异常波动点。价格趋势分析是预测未来价格走向的基础，"
                "对于农业生产规划和市场调控具有重要参考价值。"
            ),
            "monthly": (
                "月度价格分析将数据按月汇总，通过柱状图对比各月份的平均价格水平。"
                "这种分析方式能够清晰地反映出农产品价格的季节性特征，"
                "例如蔬菜类产品通常在冬季价格较高，而水果类产品在丰收季节价格相对较低。"
                "月度分析结果可为农产品的储存和销售时机选择提供决策依据。"
            ),
            "regional": (
                "地区差异分析比较了不同地区的农产品价格水平，揭示了地理位置、"
                "运输成本、当地供需关系等因素对价格的影响。通过对比图可以直观看出"
                "各地区之间的价格差异程度，这对于跨区域农产品贸易和物流规划具有指导意义。"
                "价格差异较大的地区之间存在套利空间，也反映了市场一体化程度。"
            ),
            "weather": (
                "气象影响分析通过计算气温、降雨量、湿度等气象因素与农产品价格之间的"
                "相关系数，量化了天气条件对价格的影响程度。相关性热力图以颜色深浅直观展示"
                "各变量间的关联强度。研究表明，极端天气事件（如持续高温、暴雨等）往往会"
                "导致农产品产量下降，进而推高市场价格。了解气象因素的影响有助于提前预判价格变动。"
            ),
            "volatility": (
                "价格波动分析通过计算周标准差和变异系数，衡量各农产品价格的稳定性。"
                "波动较大的产品面临更高的市场风险，需要更加审慎的库存管理和定价策略。"
                "波动分析结果可以帮助市场参与者评估风险水平，制定相应的风险管理措施，"
                "同时也为价格预测模型的不确定性估计提供参考。"
            ),
        }

        for result in results:
            atype = result.analysis_type
            if atype in section_titles:
                report_sections.append(section_titles[atype])
                report_sections.append("-" * 40)
                # 添加具体分析描述
                if result.description:
                    report_sections.append(result.description)
                # 添加通用分析说明
                if atype in section_details:
                    report_sections.append(section_details[atype])
                report_sections.append("")

        # 总结
        report_sections.append("七、总结与建议")
        report_sections.append("-" * 40)
        report_sections.append(
            "综合以上多维度分析结果，本报告得出以下主要结论：农产品价格受季节性因素、"
            "地区供需差异和气象条件等多重因素共同影响，呈现出明显的时空变化特征。"
            "建议相关部门和市场参与者关注以下几点：（1）根据价格趋势和季节性规律，"
            "合理安排农产品的种植、储存和销售计划；（2）关注气象预报信息，提前做好"
            "极端天气对农产品供应和价格影响的应对准备；（3）利用地区间价格差异，"
            "优化农产品物流配送网络，促进市场资源的合理配置；（4）基于价格波动分析结果，"
            "建立价格预警机制，降低市场风险。本分析报告的数据和结论可作为后续"
            "机器学习价格预测模型的重要参考和验证依据。"
        )
        report_sections.append("")
        report_sections.append("=" * 60)
        report_sections.append("报告生成完毕")
        report_sections.append("=" * 60)

        report = "\n".join(report_sections)
        return report

    @staticmethod
    def _translate_column(col_name: str) -> str:
        """将英文列名翻译为中文标签"""
        translations = {
            "average_price": "平均价格",
            "highest_price": "最高价格",
            "lowest_price": "最低价格",
            "average_temperature": "平均气温",
            "highest_temperature": "最高气温",
            "lowest_temperature": "最低气温",
            "rainfall": "降雨量",
            "humidity": "湿度",
            "sunshine_duration": "日照时长",
        }
        return translations.get(col_name, col_name)
