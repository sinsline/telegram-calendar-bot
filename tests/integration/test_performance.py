"""
Performance and load testing for Telegram Calendar Bot
"""

import asyncio
import time
import psutil
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.nlp_service import NLPService


class TestPerformance:
    """Performance benchmarks and load testing"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_nlp_performance_benchmark(self):
        """Benchmark NLP parsing performance"""
        nlp = NLPService()
        
        test_messages = [
            "встреча завтра в 15:00",
            "звонок клиенту в пятницу в 19:30", 
            "дентист 25 декабря в 10 утра",
            "планерка сегодня в половине четвертого",
            "обед с командой послезавтра в 12:30"
        ] * 20  # 100 total messages
        
        # Measure processing time
        start_time = time.perf_counter()
        
        for message in test_messages:
            result = await nlp.parse_event(message)
            assert result['confidence'] > 0.5
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = total_time / len(test_messages)
        
        print(f"\\nNLP Performance:")
        print(f"Total messages: {len(test_messages)}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average time per message: {avg_time:.4f}s")
        print(f"Messages per second: {len(test_messages)/total_time:.2f}")
        
        # Performance assertions
        assert avg_time < 0.1, f"NLP parsing too slow: {avg_time:.4f}s per message"
        assert len(test_messages)/total_time > 20, f"Throughput too low: {len(test_messages)/total_time:.2f} msg/s"
    
    @pytest.mark.asyncio
    @pytest.mark.slow 
    async def test_concurrent_processing(self):
        """Test concurrent message processing performance"""
        
        # Mock services for performance testing
        mock_calendar = AsyncMock()
        mock_calendar.create_event.return_value = {'id': 'test_event'}
        
        real_nlp = NLPService()
        
        async def process_message(message_id):
            """Simulate processing one message"""
            message = f"встреча {message_id} завтра в {10 + message_id % 8}:00"
            
            # NLP parsing (real)
            parsed = await real_nlp.parse_event(message)
            
            # Calendar creation (mocked)
            await mock_calendar.create_event(
                summary=parsed['summary'],
                start_time=parsed['start_time'], 
                end_time=parsed['end_time']
            )
            
            return message_id
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        
        for concurrency in concurrency_levels:
            print(f"\\nTesting concurrency level: {concurrency}")
            
            # Create tasks
            tasks = [process_message(i) for i in range(concurrency)]
            
            # Measure execution time
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.perf_counter()
            
            # Check for errors
            errors = [r for r in results if isinstance(r, Exception)]
            assert len(errors) == 0, f"Errors at concurrency {concurrency}: {errors}"
            
            total_time = end_time - start_time
            throughput = concurrency / total_time
            
            print(f"Messages: {concurrency}, Time: {total_time:.3f}s, Throughput: {throughput:.2f} msg/s")
            
            # Performance assertions
            assert total_time < 10, f"Processing {concurrency} messages took too long: {total_time:.3f}s"
            assert mock_calendar.create_event.call_count == len([r for r in results if not isinstance(r, Exception)])
            
            # Reset mock for next iteration
            mock_calendar.reset_mock()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_usage_stability(self):
        """Test memory usage under load"""
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\\nInitial memory usage: {initial_memory:.2f} MB")
        
        nlp = NLPService()
        
        # Process many messages to test for memory leaks
        for batch in range(10):
            batch_messages = [
                f"встреча {i} завтра в {10 + i % 8}:00"
                for i in range(100)
            ]
            
            for message in batch_messages:
                await nlp.parse_event(message)
            
            # Check memory usage after each batch
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            print(f"Batch {batch+1}: Memory usage: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
            
            # Memory should not increase drastically
            assert memory_increase < 100, f"Memory usage increased too much: +{memory_increase:.2f} MB"
    
    def test_service_startup_time(self):
        """Test service initialization performance"""
        
        # Test NLP service startup
        start_time = time.perf_counter()
        nlp = NLPService()
        nlp_startup_time = time.perf_counter() - start_time
        
        print(f"\\nService Startup Times:")
        print(f"NLP Service: {nlp_startup_time:.4f}s")
        
        # Startup time assertions
        assert nlp_startup_time < 1.0, f"NLP startup too slow: {nlp_startup_time:.4f}s"


class TestScalability: 
    """Tests for system scalability and resource limits"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_high_volume_processing(self):
        """Test processing high volume of messages"""
        
        mock_calendar = AsyncMock()
        mock_calendar.create_event.return_value = {'id': 'event'}
        
        nlp = NLPService()
        
        # Generate 1000 test messages
        messages = [
            f"событие {i} {['сегодня', 'завтра', 'послезавтра'][i % 3]} в {9 + i % 10}:00"
            for i in range(1000)
        ]
        
        print(f"\\nProcessing {len(messages)} messages...")
        
        start_time = time.perf_counter() 
        processed_count = 0
        
        # Process in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Process batch concurrently
            tasks = []
            for message in batch:
                async def process_msg(msg):
                    parsed = await nlp.parse_event(msg) 
                    await mock_calendar.create_event(
                        summary=parsed['summary'],
                        start_time=parsed['start_time'],
                        end_time=parsed['end_time']
                    )
                    return 1
                
                tasks.append(process_msg(message))
            
            batch_results = await asyncio.gather(*tasks)
            processed_count += len(batch_results)
            
            # Progress update
            if (i // batch_size + 1) % 5 == 0:
                elapsed = time.perf_counter() - start_time
                rate = processed_count / elapsed
                print(f"Processed {processed_count}/{len(messages)} messages ({rate:.1f} msg/s)")
        
        total_time = time.perf_counter() - start_time
        final_rate = processed_count / total_time
        
        print(f"\\nHigh Volume Results:")
        print(f"Total messages: {processed_count}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Final rate: {final_rate:.2f} msg/s")
        
        # Scalability assertions
        assert processed_count == len(messages), f"Not all messages processed: {processed_count}/{len(messages)}"
        assert final_rate > 10, f"Throughput too low for high volume: {final_rate:.2f} msg/s"
        assert total_time < 300, f"High volume processing took too long: {total_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test behavior under resource constraints"""
        
        # Test with limited memory scenario
        nlp = NLPService()
        
        # Create very long message to test memory handling
        long_message = "встреча " + "очень " * 1000 + "важная завтра в 15:00"
        
        # Should handle gracefully without crashing
        result = await nlp.parse_event(long_message)
        
        # Should still extract basic information
        assert "встреча" in result['summary']
        assert "15:00" in result['start_time'] or result['confidence'] < 0.5
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load(self):
        """Test performance under sustained load"""
        
        nlp = NLPService()
        
        # Simulate sustained load for 30 seconds
        duration = 30  # seconds
        start_time = time.perf_counter()
        processed_count = 0
        
        print(f"\\nRunning sustained load test for {duration} seconds...")
        
        while time.perf_counter() - start_time < duration:
            # Process messages continuously
            batch_tasks = []
            for i in range(10):  # Small batches
                message = f"событие {processed_count + i} завтра в {10 + i % 8}:00"
                task = nlp.parse_event(message)
                batch_tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks)
            processed_count += len(batch_results)
            
            # Brief pause to prevent overwhelming
            await asyncio.sleep(0.1)
        
        elapsed_time = time.perf_counter() - start_time
        average_rate = processed_count / elapsed_time
        
        print(f"Sustained Load Results:")
        print(f"Duration: {elapsed_time:.2f}s")  
        print(f"Messages processed: {processed_count}")
        print(f"Average rate: {average_rate:.2f} msg/s")
        
        # Sustained performance assertions
        assert average_rate > 5, f"Sustained throughput too low: {average_rate:.2f} msg/s"
        assert processed_count > 100, f"Not enough messages processed: {processed_count}"


class TestResourceUsage:
    """Tests for resource usage optimization"""
    
    def test_cpu_usage_efficiency(self):
        """Test CPU usage during processing"""
        
        # Monitor CPU during NLP processing
        nlp = NLPService()
        
        # Get initial CPU usage
        process = psutil.Process()
        initial_cpu = process.cpu_percent()
        
        # Process messages and monitor CPU
        start_time = time.time()
        messages_processed = 0
        
        # Process for 10 seconds
        while time.time() - start_time < 10:
            message = f"тест {messages_processed} завтра в 15:00"
            
            # Synchronous call for this test
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(nlp.parse_event(message))
            loop.close()
            
            messages_processed += 1
        
        final_cpu = process.cpu_percent()
        
        print(f"\\nCPU Usage Test:")
        print(f"Initial CPU: {initial_cpu:.1f}%")
        print(f"Final CPU: {final_cpu:.1f}%")
        print(f"Messages processed: {messages_processed}")
        
        # CPU usage should be reasonable
        assert final_cpu < 80, f"CPU usage too high: {final_cpu:.1f}%"
    
    @pytest.mark.asyncio
    async def test_async_efficiency(self):
        """Test async processing efficiency vs sequential"""
        
        nlp = NLPService()
        test_messages = [f"событие {i} завтра в 1{i%10}:00" for i in range(20)]
        
        # Test sequential processing
        start_time = time.perf_counter()
        for message in test_messages:
            await nlp.parse_event(message)
        sequential_time = time.perf_counter() - start_time
        
        # Test concurrent processing  
        start_time = time.perf_counter()
        tasks = [nlp.parse_event(message) for message in test_messages]
        await asyncio.gather(*tasks)
        concurrent_time = time.perf_counter() - start_time
        
        efficiency_gain = sequential_time / concurrent_time
        
        print(f"\\nAsync Efficiency Test:")
        print(f"Sequential time: {sequential_time:.4f}s")
        print(f"Concurrent time: {concurrent_time:.4f}s") 
        print(f"Efficiency gain: {efficiency_gain:.2f}x")
        
        # Concurrent should be faster (or at least not much slower)
        assert concurrent_time <= sequential_time * 1.2, "Async processing not efficient"


if __name__ == "__main__":
    # Quick performance check for development
    import asyncio
    
    async def quick_perf_test():
        print("Running quick performance test...")
        
        nlp = NLPService()
        
        start_time = time.perf_counter()
        
        # Test 50 messages
        for i in range(50):
            message = f"встреча {i} завтра в {10 + i % 8}:00"
            result = await nlp.parse_event(message)
            assert result['confidence'] > 0.5
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        print(f"Processed 50 messages in {total_time:.3f}s ({50/total_time:.1f} msg/s)")
        print("✅ Quick performance test passed!")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(quick_perf_test())
    else:
        pytest.main([__file__, "-v", "-m", "not slow"])