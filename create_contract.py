#!/usr/bin/env python3
"""创建中文劳动合同 PDF"""

# PDF 内容（使用十六进制编码中文字符）
pdf_content = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 600 >>
stream
BT
/F1 18 Tf 100 720 Td (LABOR CONTRACT) Tj
/F1 12 Tf 100 680 Td (Contract No: 2025-LABOR-001) Tj
100 650 Td (Date: January 1, 2025) Tj
100 610 Td (Party A \(Employer\): Beijing Technology Co., Ltd.) Tj
100 580 Td (Legal Representative: Zhang San) Tj
100 550 Td (Address: No.1 Zhongguancun Street, Haidian District, Beijing) Tj
100 510 Td (Party B \(Employee\): Li Si) Tj
100 480 Td (ID Number: 110101199001011234) Tj
100 450 Td (Address: No.100 Wangjing Road, Chaoyang District, Beijing) Tj
100 420 Td (Phone: 13800138000) Tj
100 380 Td (Contract Term: 3 years) Tj
100 350 Td (Start Date: January 1, 2025) Tj
100 320 Td (End Date: December 31, 2027) Tj
100 290 Td (Probation Period: 6 months) Tj
100 260 Td (Position: Software Engineer) Tj
100 230 Td (Location: Beijing) Tj
100 200 Td (Monthly Salary: RMB 20,000) Tj
100 160 Td (SIGNATURES:) Tj
100 120 Td (Party A: _________________  Date: 2025-01-01) Tj
100 90 Td (Party B: _________________  Date: 2025-01-01) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000918 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
995
%%EOF
'''

with open('/root/.openclaw/workspace/labor_contract.pdf', 'wb') as f:
    f.write(pdf_content)

print('✅ 劳动合同 PDF 已创建')
print('文件位置：/root/.openclaw/workspace/labor_contract.pdf')

import os
size = os.path.getsize('/root/.openclaw/workspace/labor_contract.pdf')
print(f'文件大小：{size} bytes ({size/1024:.2f} KB)')
