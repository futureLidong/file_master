#!/usr/bin/env python3
"""
根据真实劳动合同范本创建 PDF 合同文件
参考《中华人民共和国劳动合同法》标准格式
"""

import os

# 劳动合同完整内容（真实合同条款）
contract_content = """
劳动合同书

合同编号：2025-LABOR-001

甲方（用人单位）
单位名称：北京科技有限公司
统一社会信用代码：91110108MA01234567
法定代表人（主要负责人）：张三
联系电话：010-88888888
注册地址：北京市海淀区中关村大街 1 号
经营地址：北京市海淀区中关村大街 1 号

乙方（劳动者）
姓名：李四
性别：男
民族：汉
出生日期：1990 年 1 月 1 日
公民身份号码：110101199001011234
户籍地址：北京市朝阳区望京路 100 号
现居住地址：北京市朝阳区望京路 100 号
联系电话：13800138000
电子邮箱：lisi@example.com

根据《中华人民共和国劳动法》、《中华人民共和国劳动合同法》等法律法规，甲乙双方遵循合法、公平、平等自愿、协商一致、诚实信用的原则，订立本合同。

第一条 合同期限
1.1 本合同为固定期限劳动合同。
1.2 合同期限：3 年，自 2025 年 1 月 1 日起至 2027 年 12 月 31 日止。
1.3 其中试用期为 6 个月，自 2025 年 1 月 1 日起至 2025 年 6 月 30 日止。

第二条 工作内容和工作地点
2.1 乙方的工作岗位为：软件工程师。
2.2 乙方的工作地点为：北京。
2.3 乙方应按照甲方的合法要求，按时完成规定的工作数量，达到规定的质量标准。

第三条 工作时间和休息休假
3.1 甲方实行标准工时制度，每日工作 8 小时，每周工作 40 小时。
3.2 甲方依法保证乙方的休息休假权利。

第四条 劳动报酬
4.1 乙方月工资为人民币 20000 元（大写：贰万元整）。
4.2 试用期工资为转正工资的 80%，即人民币 16000 元。
4.3 甲方每月 10 日前以货币形式支付乙方上月工资。
4.4 甲方根据生产经营状况和依法制定的工资分配办法调整乙方工资。

第五条 社会保险和福利待遇
5.1 甲乙双方按照国家和地方有关规定参加社会保险。
5.2 甲方为乙方办理养老、医疗、失业、工伤、生育保险。
5.3 乙方个人应缴纳的社会保险费，由甲方从乙方工资中代扣代缴。

第六条 劳动保护、劳动条件和职业危害防护
6.1 甲方建立健全生产工艺流程、操作规程、工作规范和劳动安全卫生制度及其标准。
6.2 甲方对可能产生职业病危害的岗位，向乙方履行如实告知义务。
6.3 甲方为乙方提供符合国家规定的劳动安全卫生条件和必要的劳动防护用品。

第七条 劳动合同的变更、解除和终止
7.1 经甲乙双方协商一致，可以变更本合同相关内容或解除本合同。
7.2 乙方提前三十日以书面形式通知甲方，可以解除劳动合同。
7.3 甲方有下列情形之一的，乙方可以解除劳动合同：
    (一) 未按照劳动合同约定提供劳动保护或者劳动条件的；
    (二) 未及时足额支付劳动报酬的；
    (三) 未依法为乙方缴纳社会保险费的。
7.4 本合同期满，劳动合同终止。

第八条 经济补偿与赔偿
8.1 甲方违法解除或终止本合同，应向乙方支付赔偿金。
8.2 乙方违法解除劳动合同，给甲方造成损失的，应承担赔偿责任。

第九条 争议处理
9.1 甲乙双方因履行本合同发生争议，可依法申请调解、仲裁、提起诉讼。

第十条 其他约定
10.1 本合同未尽事宜，按国家和地方有关规定执行。
10.2 本合同一式两份，甲乙双方各执一份，具有同等法律效力。
10.3 本合同自甲乙双方签字或盖章之日起生效。

（以下无正文）

甲方（盖章）：北京科技有限公司          乙方（签字）：李四

法定代表人（签字）：张三

签订日期：2025 年 1 月 1 日              签订日期：2025 年 1 月 1 日

签订地点：北京市海淀区
"""

def create_pdf():
    """创建 PDF 文件"""
    
    # PDF 文档结构
    objects = []
    xref = []
    current_offset = 0
    
    # 1. PDF 头
    header = b"%PDF-1.4\n"
    objects.append(header)
    xref.append(current_offset)
    current_offset += len(header)
    
    # 2. 目录对象
    catalog = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    objects.append(catalog)
    xref.append(current_offset)
    current_offset += len(catalog)
    
    # 3. 页面树对象
    pages = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    objects.append(pages)
    xref.append(current_offset)
    current_offset += len(pages)
    
    # 4. 页面内容（分行处理）
    lines = contract_content.strip().split('\n')
    content_stream = "BT\n/F1 12 Tf 50 750 Td\n"
    
    y_position = 750
    for line in lines:
        # 转义特殊字符
        line = line.replace('(', '\\(').replace(')', '\\)')
        content_stream += f"50 {y_position} Td ({line}) Tj\n"
        y_position -= 15
        if y_position < 50:  # 新页面
            content_stream += "ET\nendstream\nendobj\n"
            # 这里简化处理，只创建单页
    
    content_stream += "ET\n"
    
    page_content = f"4 0 obj\n<< /Length {len(content_stream.encode('utf-8'))} >>\nstream\n{content_stream}\nendstream\nendobj\n".encode('utf-8')
    objects.append(page_content)
    xref.append(current_offset)
    current_offset += len(page_content)
    
    # 5. 页面对象
    page = b"""3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
"""
    objects.append(page)
    xref.append(current_offset)
    current_offset += len(page)
    
    # 6. 字体对象
    font = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    objects.append(font)
    xref.append(current_offset)
    current_offset += len(font)
    
    # 7. xref 表
    xref_start = current_offset
    xref_content = f"xref\n0 {len(objects) + 1}\n"
    xref_content += "0000000000 65535 f \n"
    for offset in xref:
        xref_content += f"{offset:010d} 00000 n \n"
    
    objects.append(xref_content.encode('utf-8'))
    current_offset += len(xref_content.encode('utf-8'))
    
    # 8. trailer
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n"
    objects.append(trailer.encode('utf-8'))
    
    # 写入文件
    output_path = '/root/.openclaw/workspace/labor_contract_real.pdf'
    with open(output_path, 'wb') as f:
        for obj in objects:
            if isinstance(obj, bytes):
                f.write(obj)
            else:
                f.write(obj.encode('utf-8'))
    
    return output_path

if __name__ == "__main__":
    output_path = create_pdf()
    print("✅ 劳动合同 PDF 已创建")
    print(f"📄 文件位置：{output_path}")
    print(f"📦 文件大小：{os.path.getsize(output_path) / 1024:.2f} KB")
    print("\n📋 合同主要内容:")
    print("=" * 60)
    for line in contract_content.strip().split('\n')[:20]:
        print(line)
    print("...")
    print("=" * 60)
