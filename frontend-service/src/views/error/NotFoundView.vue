<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-image">
        <div class="error-code">404</div>
      </div>
      <div class="error-text">
        <h2>页面未找到</h2>
        <p>抱歉，您访问的页面不存在或已被移动</p>
      </div>
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          返回首页
        </el-button>
        <el-button @click="goBack">
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.back()
}
</script>

<style lang="scss" scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  .not-found-content {
    text-align: center;
    color: white;
    
    .error-image {
      margin-bottom: 32px;
      
      .error-code {
        font-size: 120px;
        font-weight: bold;
        line-height: 1;
        opacity: 0.8;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
      }
    }
    
    .error-text {
      margin-bottom: 32px;
      
      h2 {
        margin: 0 0 16px 0;
        font-size: 32px;
        font-weight: 600;
      }
      
      p {
        margin: 0;
        font-size: 16px;
        opacity: 0.9;
      }
    }
    
    .error-actions {
      display: flex;
      gap: 16px;
      justify-content: center;
    }
  }
}

@media (max-width: 768px) {
  .not-found {
    .not-found-content {
      padding: 20px;
      
      .error-image {
        .error-code {
          font-size: 80px;
        }
      }
      
      .error-text {
        h2 {
          font-size: 24px;
        }
        
        p {
          font-size: 14px;
        }
      }
      
      .error-actions {
        flex-direction: column;
        align-items: center;
        
        .el-button {
          width: 200px;
        }
      }
    }
  }
}
</style> 