# Import Node.js v24 image
FROM node:24-alpine

# Create working directory 
WORKDIR /app

# Copy dependencies files
COPY package*.json .

# Install dependencies
RUN npm install

# Copy all code
COPY . .

# Use localhost port 5173 
EXPOSE 5173

# Run app
CMD [ "npm", "run", "dev", "--", "--host", "0.0.0.0" ]