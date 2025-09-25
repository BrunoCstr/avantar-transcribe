import fs from 'fs';
import path from 'path';

// URL da API otimizada no EasyPanel
const API_BASE_URL = 'https://avantar-tools-avantar-transcribe.dhyhg5.easypanel.host';

// Exemplo otimizado para diferentes tipos de arquivo
async function testTranscription() {
    
    // 1. Verificar saúde da API
    console.log('🏥 Verificando saúde da API...');
    await checkHealth();
    
    // 2. Teste com áudio do WhatsApp (otimizado)
    console.log('🎵 Testando áudio do WhatsApp...');
    await testWhatsAppAudio();
    
    // 3. Teste com vídeo
    console.log('🎥 Testando vídeo...');
    await testVideo();
    
    // 4. Teste de cache
    console.log('💾 Testando cache...');
    await testCache();
    
    // 5. Teste OCR
    console.log('📷 Testando OCR...');
    await testOCR();
    
    // 6. Verificar estatísticas
    console.log('📊 Verificando estatísticas...');
    await checkStats();
}

async function parseJsonOrThrow(response) {
    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        throw new Error(`HTTP ${response.status} - falha ao parsear JSON`);
    }
    if (!response.ok) {
        const detail = data?.detail || data?.error || JSON.stringify(data);
        throw new Error(`HTTP ${response.status} - ${detail}`);
    }
    return data;
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await parseJsonOrThrow(response);
        
        console.log('✅ API Health:', {
            status: health.status,
            cpu: health.resources.cpu_percent + '%',
            memory: health.resources.memory_percent + '%',
            available_memory: health.resources.memory_available_mb + 'MB',
            max_file_size: health.max_file_size_mb + 'MB',
            ocr_available: health.ocr_available
        });
        
    } catch (error) {
        console.error('❌ Erro ao verificar saúde:', error.message);
    }
}

async function testWhatsAppAudio() {
    try {
        const audioBuffer = fs.readFileSync('./test-archives/audio.ogg');
        
        const formData = new FormData();
        formData.append('file', new Blob([audioBuffer], { type: 'audio/ogg' }), 'whatsapp-audio.ogg');
        
        const response = await fetch(`${API_BASE_URL}/transcribe-simple`, {
            method: 'POST',
            body: formData
        });
        const result = await parseJsonOrThrow(response);
        console.log('✅ WhatsApp:', result?.text ? {
            text: result.text,
            processing_time: 'N/A (simple endpoint)'
        } : { raw: result });
        
    } catch (error) {
        console.error('❌ Erro no WhatsApp:', error.message);
    }
}

async function testVideo() {
    try {
        // Simular um vídeo (você pode substituir por um arquivo real)
        const videoPath = './test-archives/video.mp4';
        
        if (fs.existsSync(videoPath)) {
            const videoBuffer = fs.readFileSync(videoPath);
            
            const formData = new FormData();
            formData.append('file', new Blob([videoBuffer], { type: 'video/mp4' }), 'sample.mp4');
            formData.append('language', 'pt');
            
            const response = await fetch(`${API_BASE_URL}/transcribe`, {
                method: 'POST',
                body: formData
            });
            const result = await parseJsonOrThrow(response);
            console.log('✅ Vídeo:', result?.text ? {
                text: (result.text || '').substring(0, 100) + '...',
                model: result.model_used,
                duration: result.duration,
                cached: result.cached
            } : { raw: result });
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
        const audioBuffer = fs.readFileSync('./test-archives/audio.ogg');
        
        const formData = new FormData();
        formData.append('file', new Blob([audioBuffer], { type: 'audio/ogg' }), 'whatsapp-audio.ogg');
        
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/transcribe`, {
            method: 'POST',
            body: formData
        });
        const endTime = Date.now();
        
        const result = await parseJsonOrThrow(response);
        console.log('✅ Cache test:', result?.text ? {
            cached: result.cached,
            processing_time: `${endTime - startTime}ms`,
            text_preview: (result.text || '').substring(0, 50) + '...',
            model_used: result.model_used
        } : { raw: result, processing_time: `${endTime - startTime}ms` });
        
    } catch (error) {
        console.error('❌ Erro no teste de cache:', error.message);
    }
}

async function testOCR() {
    try {
        // Teste de OCR com imagem
        const imagePath = './test-archives/imagem.png';
        
        if (fs.existsSync(imagePath)) {
            const imageBuffer = fs.readFileSync(imagePath);
            
            const formData = new FormData();
            formData.append('file', new Blob([imageBuffer], { type: 'image/jpeg' }), 'sample.jpg');
            
            const response = await fetch(`${API_BASE_URL}/ocr/image`, {
                method: 'POST',
                body: formData
            });
            
            const result = await parseJsonOrThrow(response);
            console.log('✅ OCR:', {
                text: (result.text || '').substring(0, 100) + '...',
                method: result.method,
                confidence: result.confidence,
                cached: result.cached
            });
        } else {
            console.log('⚠️  Arquivo de imagem não encontrado, pulando teste OCR');
        }
        
    } catch (error) {
        console.error('❌ Erro no OCR:', error.message);
    }
}

async function checkStats() {
    try {
        // Verificar estatísticas do cache
        const cacheResponse = await fetch(`${API_BASE_URL}/cache/stats`);
        const cache = await parseJsonOrThrow(cacheResponse);
        
        console.log('✅ Cache Stats:', {
            cache_items: cache.cache_size,
            max_cache_size: cache.max_cache_size,
            cache_memory: cache.memory_usage_mb.toFixed(2) + 'MB',
            cpu_percent: cache.resources.cpu_percent + '%',
            memory_percent: cache.resources.memory_percent + '%'
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