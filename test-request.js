import fs from 'fs';
import path from 'path';

// Exemplo otimizado para diferentes tipos de arquivo
async function testTranscription() {
    
    // 1. Teste com áudio do WhatsApp (otimizado)
    console.log('🎵 Testando áudio do WhatsApp...');
    await testWhatsAppAudio();
    
    // 2. Teste com vídeo grande
    console.log('🎥 Testando vídeo...');
    await testVideo();
    
    // 3. Teste de cache
    console.log('💾 Testando cache...');
    await testCache();
    
    // 4. Verificar estatísticas
    console.log('📊 Verificando estatísticas...');
    await checkStats();
}

async function testWhatsAppAudio() {
    try {
        const audioBuffer = fs.readFileSync('./audios/WhatsApp-Ptt-2025-09-19-at-12.25.16.ogg');
        
        const formData = new FormData();
        formData.append('file', new Blob([audioBuffer], { type: 'audio/ogg' }), 'whatsapp-audio.ogg');
        
        const response = await fetch('http://localhost:8000/transcribe-whatsapp', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('✅ WhatsApp:', {
            text: result.text,
            model: result.model_used,
            duration: result.duration,
            cached: result.cached
        });
        
    } catch (error) {
        console.error('❌ Erro no WhatsApp:', error.message);
    }
}

async function testVideo() {
    try {
        // Simular um vídeo (você pode substituir por um arquivo real)
        const videoPath = './videos/sample.mp4';
        
        if (fs.existsSync(videoPath)) {
            const videoBuffer = fs.readFileSync(videoPath);
            
            const formData = new FormData();
            formData.append('file', new Blob([videoBuffer], { type: 'video/mp4' }), 'sample.mp4');
            formData.append('language', 'pt');
            
            const response = await fetch('http://localhost:8000/transcribe-video', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            console.log('✅ Vídeo:', {
                text: result.text.substring(0, 100) + '...',
                model: result.model_used,
                duration: result.duration
            });
        } else {
            console.log('⚠️  Arquivo de vídeo não encontrado, pulando teste');
        }
        
    } catch (error) {
        console.error('❌ Erro no vídeo:', error.message);
    }
}

async function testCache() {
    try {
        // Testar o mesmo arquivo novamente para verificar cache
        const audioBuffer = fs.readFileSync('./audios/WhatsApp-Ptt-2025-09-19-at-12.25.16.ogg');
        
        const formData = new FormData();
        formData.append('file', new Blob([audioBuffer], { type: 'audio/ogg' }), 'whatsapp-audio.ogg');
        
        const startTime = Date.now();
        const response = await fetch('http://localhost:8000/transcribe-whatsapp', {
            method: 'POST',
            body: formData
        });
        const endTime = Date.now();
        
        const result = await response.json();
        console.log('✅ Cache test:', {
            cached: result.cached,
            processing_time: `${endTime - startTime}ms`,
            text_preview: result.text.substring(0, 50) + '...'
        });
        
    } catch (error) {
        console.error('❌ Erro no teste de cache:', error.message);
    }
}

async function checkStats() {
    try {
        // Verificar saúde da API
        const healthResponse = await fetch('http://localhost:8000/health');
        const health = await healthResponse.json();
        
        // Verificar estatísticas do cache
        const cacheResponse = await fetch('http://localhost:8000/cache/stats');
        const cache = await cacheResponse.json();
        
        console.log('✅ Status da API:', {
            status: health.status,
            models: health.models_loaded,
            max_file_size: health.max_file_size_mb + 'MB',
            cache_items: cache.cache_size,
            cache_memory: cache.memory_usage_mb.toFixed(2) + 'MB'
        });
        
    } catch (error) {
        console.error('❌ Erro ao verificar stats:', error.message);
    }
}

// Executar testes
testTranscription().then(() => {
    console.log('🎉 Testes concluídos!');
}).catch(error => {
    console.error('💥 Erro geral:', error);
});