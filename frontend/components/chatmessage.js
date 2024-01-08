import React, { useState, useEffect } from 'react'

import { CopyOutlined, CheckOutlined } from '@ant-design/icons';
import { UserOutlined, MessageTwoTone } from '@ant-design/icons';
import { LikeOutlined, DislikeOutlined } from '@ant-design/icons';
import { ConfigProvider, theme, Typography  } from 'antd';
import { Card, Flex, Space, Modal } from 'antd';
import { Avatar, Input, Button, Spin, Skeleton, Tag } from 'antd';

import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter'
import { vscDarkPlus, coyWithoutShadows, darcula } from 'react-syntax-highlighter/dist/esm/styles/prism'

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

import styles from '../styles/markdown.module.css'

let codeTheme = vscDarkPlus

codeTheme['pre[class*="language-"]'].margin = '0 0 .5em 0';
codeTheme['pre[class*="language-"]'].borderRadius = '0 0 .375rem .375rem'
codeTheme['pre[class*="language-"]'].fontSize = '0.7rem'

function Markdown ( {children} ) {
    return (
        <ReactMarkdown className={styles.markdown} rehypePlugins={[rehypeHighlight, remarkGfm, rehypeRaw]} 
            components={{
                code({node, inline, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '')
                    return !inline && match ? (
                        <Flex vertical>
                        <div className={styles.codeTitle}>
                            <Text className={styles.codeTitleText}>Language: {match[1].toLocaleUpperCase()}</Text>
                        </div>
                        <SyntaxHighlighter
                            // showLineNumbers={true}
                            wrapLongLines={true}
                            {...props}
                            style={codeTheme}
                            language={match[1]}
                            PreTag="div"
                        >
                            {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                        </Flex>
                    ) : (
                        <code {...props} className={className}>
                        {children}
                        </code>
                    )
                }
            }}
        >
        {children}
        </ReactMarkdown>
    )
}

function Feedback ( {query_id, response, callback} ) {
    const [rating, setRating] = useState(-1);
    const [reason, setReason] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [copyIcon, setCopyIcon] = useState(< CopyOutlined />);
    const rateLike = () => {
        setRating(1);
        setIsModalOpen(true);
    };
    const rateDislike = () => {
        setRating(0);
        setIsModalOpen(true);
    }
    const ratingOk = () => {
        setIsModalOpen(false);
        callback({
            query_id: query_id,
            feedback_dict: {
                type: 'thumb',
                score: rating,
                comment: reason
            }
        });
        setReason('');
    };
    const ratingCancel = () => {
        setRating(-1);
        setIsModalOpen(false);
    }

    const copyResponse = () => {
        navigator.clipboard.writeText(response).then(() => {
            setCopyIcon(< CheckOutlined />);
        });
    }
    useEffect(() => {
        const timer = setTimeout(() => {setCopyIcon(< CopyOutlined />)}, 1000);
        return () => {clearTimeout(timer);}
    }, [copyIcon]);

    return (
        <>
        <Flex gap='5px'>
            { rating !== 0 ? (<Button type='text' size='small' icon={< LikeOutlined />} onClick={rateLike} disabled={rating === 1} />) : ('')}
            { rating !== 1 ? (<Button type='text' size='small' icon={< DislikeOutlined />} onClick={rateDislike} disabled={rating === 0} />) : ('')}
            <Button type='text' size='small' icon={ copyIcon } onClick={copyResponse} />
        </Flex>
        <Modal
            title="评价详细信息" okText='提交' cancelText='取消'
            open={isModalOpen}
            onOk={ratingOk}
            onCancel={ratingCancel}>
            <p>请在下面的文本框中写下{rating === 1 ? '认同' : '不认同'}的具体原因</p>
            <TextArea 
                value={ reason }
                onChange={ (e) => setReason(e.target.value) }/>
        </Modal>
        </>
    )
}

function UserMessage( {query_id, title, texts } ) {
    return (
        <Card bordered={false} style={{ padding: '0', background: '#CFEDCF'}}>
        <Flex gap='small'>
            <div><Avatar size="small" style={{ backgroundColor: '#87d068' }} icon={<UserOutlined /> }/></div>
            <div style={{width: '100%', fontWeight: 300, fontSize: ''}}>
            <Flex vertical >
                <Title level={5} style={{margin: 0}}>{title}</Title>
                {...texts.map((text, index) => {
                    const keyBody = query_id+'_'+index;
                    return (<Paragraph>
                        <Text key={keyBody} style={{fontSize: 'medium'}}>{text}</Text>
                    </Paragraph>)
                })}
            </Flex>
            </div>
        </Flex>
        </Card>
    );
}

UserMessage.defaultProps = {
    title: 'You'
};

function AssistantMessage( { title, children, response, query_id, spinning, onFeedback} ) {
    return (
        <Card bordered={false} style={{ padding: '0', background: '#FFFFFF'}}>
        <Flex gap='small'>
            <div><Avatar size="small" style={{ backgroundColor: '#1677ff' }} icon={<MessageTwoTone />}/></div>
            <div style={{width: '100%'}}>
                <Title level={5} style={{margin: 0}}>{title}</Title>
                <div style={{padding: '5px 0'}} >
                    <Markdown>{response}</Markdown>
                    {/* <Spin spinning={spinning} >
                    {spinning ? <Skeleton active /> : ''}
                    </Spin> */}
                    <Feedback
                        query_id={ query_id }
                        response={ response }
                        callback={ onFeedback }/>
                </div>
                {children}
            </div>
        </Flex>
        </Card>
    );
}

AssistantMessage.defaultProps = {
    title: 'LLM',
    spinning: false
};

export default function ChatMessage( props ) {
    return (
        <ConfigProvider theme={{algorithm: theme.defaultAlgorithm}}>
        { (props.role === 'user') ? (<UserMessage {...props} />) : <AssistantMessage {...props} />}
        </ConfigProvider>
    );
}