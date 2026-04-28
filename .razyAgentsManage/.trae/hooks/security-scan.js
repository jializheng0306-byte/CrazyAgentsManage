/**
 * Security Scan - 基础安全扫描
 * 
 * 对应 ECC Hook: pre:governance-capture (部分功能)
 * 触发时机: 代码生成/写入前
 * 
 * 功能:
 * - 检测硬编码密钥和凭据
 * - 检测 SQL 注入风险模式
 * - 检测不安全的函数调用
 */

module.exports = function securityScan(context) {
  const { filePath, content } = context;
  const vulnerabilities = [];
  
  // 1. 密钥/凭据检测
  const secretPatterns = [
    { regex: /(?:api[_-]?key|apikey|secret[_-]?key|password|token)\s*[:=]\s*["'][^"']{10,}["']/gi, label: '硬编码密钥', severity: 'critical' },
    { regex: /(?:aws_access_key_id|aws_secret_access_key)\s*[:=]\s*["'][^"']+/gi, label: 'AWS 凭据', severity: 'critical' },
    { regex: /(?:mongodb|mysql|postgres|redis)?:\/\/[^:]+:[^@]+@/gi, label: '数据库连接字符串', severity: 'high' },
    { regex: /-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----/g, label: '私钥', severity: 'critical' }
  ];
  
  secretPatterns.forEach(({ regex, label, severity }) => {
    if (regex.test(content)) {
      vulnerabilities.push({
        type: 'secret',
        label,
        severity,
        message: `🔴 ${severity.toUpperCase()}: 检测到可能的 ${label}`,
        fix: '使用环境变量或密钥管理服务（如 AWS Secrets Manager、Vault）'
      });
    }
  });
  
  // 2. SQL 注入风险（简化版）
  if (/\$\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE)/i.test(content)) {
    vulnerabilities.push({
      type: 'sql-injection',
      label: 'SQL 注入风险',
      severity: 'high',
      message: '⚠️ HIGH: 可能的 SQL 注入漏洞（字符串拼接查询）',
      fix: '使用参数化查询或 ORM 方法'
    });
  }
  
  // 3. 不安全函数检测
  const unsafeFunctions = [
    { pattern: /eval\s*\(/g, label: 'eval()', severity: 'medium' },
    { pattern: /innerHTML\s*=/g, label: 'innerHTML 赋值', severity: 'medium' },
    { pattern: /document\.write\s*\(/g, label: 'document.write()', severity: 'low' }
  ];
  
  unsafeFunctions.forEach(({ pattern, label, severity }) => {
    if (pattern.test(content)) {
      vulnerabilities.push({
        type: 'unsafe-function',
        label,
        severity,
        message: `⚡ ${severity.toUpperCase()}: 使用了不安全函数 ${label}`,
        suggestion: `查找 ${label} 的安全替代方案`
      });
    }
  });
  
  if (vulnerabilities.length === 0) {
    return { status: 'ok', message: '✅ 安全扫描通过' };
  }
  
  const hasCritical = vulnerabilities.some(v => v.severity === 'critical');
  
  return {
    status: hasCritical ? 'blocked' : 'warning',
    vulnerabilities,
    summary: `发现 ${vulnerabilities.length} 个安全问题`,
    actionRequired: hasCritical ? '必须修复后才能继续' : '建议尽快修复'
  };
};
