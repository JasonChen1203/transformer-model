from tensorflow.keras.layers import Layer, Dense
from tensorflow import shape, reshape, transpose
from ScaledDotProductAttention import ScaledDotProductAttention



class MultiheadAttention(Layer):
    """
    MultiheadAttention(Q, K, V) = Concat(head_1, head_2, ..., head_h)W^O, where head_i = Attention(QW_i^Q, KW_i^K, VW_i^V),
    W_i^Q, W_i^K, W_i^V, W^O are the parameter matrices

    To compute the result in parallel, we reshape the dimensionality of Q, K, V before feeding it to ScaledDotProductAttention

    Below are the calculation of tensor shapes (taking the default values):
        for input shape = (batch size, ..., input dim), output shape for dense layer = (batch size, ..., units)
        shape(queries) = (batch size, input seq length, d_k); this is the input_shape
        W_q = Dense(d_k) => units = d_k

        Calculating shapes of q, k, v:
        shape(W_q(queries)) = (batch size, input seq length, d_k)
        => after reshape(q, shape=[batch_size, q_len, h, -1]), shape = (batch_size, seq_len, h, d_k/h)
        => after transposing, shape = (batch_size, h, seq_len, d_k/h)
        => shape(q) = shape(k) = shape(v) = (batch_size, h, seq_len, d_k/h) before feeding into ScaledDotProductAttention

        Calculating shape of output:
        shape(o) = (64, 8, 5, 5) after ScaledDotProductAttention
        => shape(o) = (batch_size, h, seq_len, d_k/h) after transpose
        => shape(output) = (batch_size, seq_len, d_k)
    """
    
    def __init__(self, h = 8, d_k = 64, d_v = 64, d_model = 512, **kwargs):
        super(MultiheadAttention, self).__init__(**kwargs)
        self.h = h
        self.d_k = d_k
        self.d_v = d_v
        self.d_model = d_model

        self.W_queries = Dense(d_k)
        self.W_keys = Dense(d_k)
        self.W_values = Dense(d_v)
        self.W_output = Dense(d_model)
        self.attention = ScaledDotProductAttention()
    

    def call(self, queries, keys, values, is_masking=False):
        h, d_k, d_v, d_model = self.h, self.d_k, self.d_v, self.d_model
        batch_size, q_len, k_len, v_len = shape(queries)[0], shape(queries)[1], shape(keys)[1], shape(values)[1]

        # linear project the queries, keys, and values
        q = self.W_queries(queries)
        k = self.W_keys(keys)
        v = self.W_values(values)

        # reshape tensors such that different heads are separated; (batch_size, len, (h*col)) => (batch_size, len, h, col)
        q = reshape(q, shape=[batch_size, q_len, h, -1])
        k = reshape(k, shape=[batch_size, k_len, h, -1])
        v = reshape(v, shape=[batch_size, v_len, h, -1])

        # transpose for dot product attention
        q = transpose(q, perm=[0, 2, 1, 3])
        k = transpose(k, perm=[0, 2, 1, 3])
        v = transpose(v, perm=[0, 2, 1, 3])

        # apply dot product attention
        o = self.attention(q, k, v, d_k, is_masking)

        # reshape the output tensor back to original
        o = transpose(o, perm=[0, 2, 1, 3])
        output = reshape(o, shape=[batch_size, shape(o)[1], d_v])

        # linear project the output to have dimension d_model
        output = self.W_output(output)

        return output
        
